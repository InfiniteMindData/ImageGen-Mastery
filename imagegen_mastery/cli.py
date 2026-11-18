"""Command line entry points. Offline by default."""

import argparse
import json
import sys
from pathlib import Path

from .capabilities import ImageSettings, capabilities
from .editing import render
from .evaluation import evaluate
from .inspection import inspect_image
from .prompt import optimize
from .reporting import make_report
from .providers import generate
from .workflow import run_loop


def _brief(path):
    return optimize(json.loads(path.read_text(encoding="utf-8")))


def main(argv=None):
    parser = argparse.ArgumentParser(prog="imagegen-mastery")
    commands = parser.add_subparsers(dest="command", required=True)
    optimize_cmd = commands.add_parser("optimize", help="compile a JSON brief to text")
    optimize_cmd.add_argument("brief", type=Path)
    review = commands.add_parser("evaluate", help="measure an image and prepare a review")
    review.add_argument("image", type=Path)
    review.add_argument("--reference", type=Path)
    report = commands.add_parser("report", help="write an offline comparison report")
    report.add_argument("image", type=Path)
    report.add_argument("--reference", type=Path, required=True)
    report.add_argument("--output-dir", type=Path, required=True)
    report.add_argument("--ssim", action="store_true")
    report.add_argument("--perceptual", action="store_true")
    report.add_argument("--require-text", action="append", default=[])
    report.add_argument("--region", type=float, nargs=4, action="append", default=[],
                        metavar=("LEFT", "TOP", "RIGHT", "BOTTOM"))
    vision = commands.add_parser("inspect", help="inspect actual pixels via a paid vision model")
    vision.add_argument("image", type=Path)
    vision.add_argument("--brief", type=Path)
    vision.add_argument("--reference", type=Path, action="append", default=[])
    vision.add_argument("--lock", action="append", default=[])
    vision.add_argument("--authorize-paid", action="store_true")
    loop = commands.add_parser("revise", help="generate or import, inspect and revise within a standard USD budget")
    loop.add_argument("brief", type=Path)
    loop.add_argument("--run-dir", type=Path, required=True)
    loop.add_argument("--start", type=Path)
    loop.add_argument("--reference", type=Path, action="append", default=[])
    loop.add_argument("--max-revisions", type=int, required=True)
    loop.add_argument("--budget-usd", required=True)
    loop.add_argument("--aspect-ratio")
    loop.add_argument("--size")
    loop.add_argument("--authorize-paid", action="store_true")
    gen = commands.add_parser("generate", help="send a compiled brief to a paid API")
    edit = commands.add_parser("edit", help="edit a source image using a paid provider")
    edit.add_argument("source", type=Path)
    edit.add_argument("--mask", type=Path)
    commands.add_parser("capabilities", help="list registered image models and settings")
    for cmd in (gen, edit):
        cmd.add_argument("brief", type=Path)
        cmd.add_argument("--provider", choices=("openai", "google"), required=True)
        cmd.add_argument("--model", required=True)
        cmd.add_argument("--output", type=Path, required=True)
        cmd.add_argument("--reference", type=Path, action="append", default=[])
        cmd.add_argument("--aspect-ratio")
        cmd.add_argument("--size")
        cmd.add_argument("--quality")
        cmd.add_argument("--authorize-paid", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.command == "optimize":
            print(_brief(args.brief))
        elif args.command == "evaluate":
            print(json.dumps(evaluate(args.image, args.reference), indent=2))
        elif args.command == "report":
            make_report(args.image, args.reference, args.output_dir, ssim=args.ssim, perceptual=args.perceptual,
                        regions=args.region, required_text=args.require_text)
            print(args.output_dir / "report.html")
        elif args.command == "inspect":
            requirements = [_brief(args.brief)] if args.brief else ["Inspect visible rendering defects."]
            print(json.dumps(inspect_image(args.image, requirements, references=args.reference,
                                           locks=args.lock, authorized=args.authorize_paid), indent=2))
        elif args.command == "revise":
            brief = json.loads(args.brief.read_text(encoding="utf-8"))
            result = run_loop(brief, args.run_dir, start=args.start, references=args.reference,
                              max_revisions=args.max_revisions, budget=args.budget_usd, aspect_ratio=args.aspect_ratio,
                              size=args.size, authorized=args.authorize_paid)
            print(json.dumps(result, indent=2))
        elif args.command == "capabilities":
            print(json.dumps(capabilities(), indent=2))
        else:
            settings = ImageSettings(getattr(args, "source", None), tuple(args.reference),
                                     getattr(args, "mask", None), args.aspect_ratio, args.size, args.quality)
            prompt = _brief(args.brief)
            # Reserve the destination before sending a billable request.
            destination = args.output.open("xb")
            try:
                with destination as stream:
                    if args.command == "generate" and settings == ImageSettings():
                        stream.write(generate(args.provider, args.model, prompt))
                    else:
                        stream.write(render(args.provider, args.model, prompt, settings,
                                            authorized=args.authorize_paid))
            except BaseException:
                args.output.unlink(missing_ok=True)
                raise
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0
