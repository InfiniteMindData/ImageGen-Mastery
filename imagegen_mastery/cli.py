"""Command line entry points. Offline by default."""

import argparse
import json
import sys
from pathlib import Path

from .acceptance import EditPolicy
from .capabilities import ImageSettings, capabilities
from .editing import render
from .evaluation import evaluate
from .inspection import inspect_image, require_authorization
from .profiles import IMAGE_PROFILES, VISION_PROFILES, PRICING_VERSION
from .prompt import optimize, review_requirements
from .references import attachment_note, bind_references
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
    vision.add_argument("--provider", choices=("openai", "google"), default="openai")
    vision.add_argument("--model")
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
    loop.add_argument("--image-provider", choices=("openai", "google"), default="google")
    loop.add_argument("--image-model")
    loop.add_argument("--vision-provider", choices=("openai", "google"), default="openai")
    loop.add_argument("--vision-model")
    loop.add_argument("--feather", type=int, default=0, metavar="PIXELS")
    loop.add_argument("--max-boundary-jump", type=float)
    loop.add_argument("--protect-region", type=float, nargs=4, action="append", default=[])
    loop.add_argument("--require-text", action="append", default=[])
    loop.add_argument("--expected-size", type=int, nargs=2, metavar=("WIDTH", "HEIGHT"))
    loop.add_argument("--authorize-paid", action="store_true")
    gen = commands.add_parser("generate", help="send a compiled brief to a paid API")
    edit = commands.add_parser("edit", help="edit a source image using a paid provider")
    edit.add_argument("source", type=Path)
    edit.add_argument("--mask", type=Path)
    commands.add_parser("capabilities", help="list registered image models and settings")
    commands.add_parser("profiles", help="list supported budgeted revision models and per-call USD reservations")
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
    for cmd in (gen, edit, vision, loop):
        cmd.add_argument("--named-reference", nargs=2, action="append", default=[], metavar=("LABEL", "PATH"))
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
            brief = json.loads(args.brief.read_text(encoding="utf-8")) if args.brief else {"intent": "Inspect visible rendering defects."}
            optimize(brief)
            refs, labels = bind_references(brief, args.reference, args.named_reference)
            locks = list(dict.fromkeys([*brief.get("locked_attributes", []), *args.lock]))
            print(json.dumps(inspect_image(args.image, review_requirements(brief), references=refs,
                                           reference_labels=labels, locks=locks, provider=args.provider,
                                           model=args.model, authorized=args.authorize_paid), indent=2))
        elif args.command == "revise":
            brief = json.loads(args.brief.read_text(encoding="utf-8"))
            policy = EditPolicy(args.feather, tuple(tuple(region) for region in args.protect_region),
                                args.max_boundary_jump, tuple(args.require_text),
                                tuple(args.expected_size) if args.expected_size else None)
            result = run_loop(brief, args.run_dir, start=args.start, references=args.reference,
                              named_references=args.named_reference, max_revisions=args.max_revisions,
                              budget=args.budget_usd, aspect_ratio=args.aspect_ratio, policy=policy,
                              image_provider=args.image_provider, image_model=args.image_model,
                              vision_provider=args.vision_provider, vision_model=args.vision_model,
                              size=args.size, authorized=args.authorize_paid)
            print(json.dumps(result, indent=2))
        elif args.command == "profiles":
            rates = {role: [{"provider": entry.provider, "model": entry.model, "reserve_usd": str(entry.reserve)}
                            for entry in entries.values()]
                     for role, entries in (("image", IMAGE_PROFILES), ("vision", VISION_PROFILES))}
            print(json.dumps({"pricing_profile": PRICING_VERSION, **rates}, indent=2))
        elif args.command == "capabilities":
            print(json.dumps(capabilities(), indent=2))
        else:
            brief = json.loads(args.brief.read_text(encoding="utf-8"))
            prompt = optimize(brief)
            refs, labels = bind_references(brief, args.reference, args.named_reference)
            settings = ImageSettings(getattr(args, "source", None), refs,
                                     getattr(args, "mask", None), args.aspect_ratio, args.size, args.quality)
            prompt += attachment_note(labels, source=settings.source is not None)
            require_authorization(args.authorize_paid)
            # Reserve the destination before sending a billable request.
            destination = args.output.open("xb")
            try:
                with destination as stream:
                    if args.command == "generate" and settings == ImageSettings():
                        stream.write(generate(args.provider, args.model, prompt, authorized=args.authorize_paid))
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
