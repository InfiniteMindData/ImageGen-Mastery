"""Command line entry points. Only generate contacts an image provider."""

import argparse
import json
import sys
from pathlib import Path

from .evaluation import evaluate
from .prompt import optimize
from .providers import generate


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
    gen = commands.add_parser("generate", help="send a compiled brief to a paid API")
    gen.add_argument("brief", type=Path)
    gen.add_argument("--provider", choices=("openai", "google"), required=True)
    gen.add_argument("--model", required=True)
    gen.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "optimize":
            print(_brief(args.brief))
        elif args.command == "evaluate":
            print(json.dumps(evaluate(args.image, args.reference), indent=2))
        else:
            prompt = _brief(args.brief)
            # Reserve the destination before sending a billable request.
            destination = args.output.open("xb")
            try:
                with destination as stream:
                    stream.write(generate(args.provider, args.model, prompt))
            except BaseException:
                args.output.unlink(missing_ok=True)
                raise
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0
