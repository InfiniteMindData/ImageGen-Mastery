"""Associate uploaded files with brief labels explicitly; brief strings are never file paths."""

import json
from pathlib import Path
from typing import Sequence


def bind_references(brief: dict, paths: Sequence[Path], named: Sequence[tuple[str, Path]],
                    *, require_all: bool = False) -> tuple[tuple[Path, ...], tuple[str, ...]]:
    declared = [entry["image"] for entry in brief.get("references", [])]
    labels = [name for name, _ in named]
    if any(not name.strip() for name in labels) or len(labels) != len(set(labels)):
        raise ValueError("Give each named reference a unique nonblank label.")
    missing = set(declared) - set(labels)
    if missing and (paths or require_all):
        raise ValueError("Bind brief references explicitly with --named-reference LABEL PATH: " + ", ".join(sorted(missing)))
    if len(declared) != len(set(declared)) and (paths or named or require_all):
        raise ValueError("Give each brief reference a distinct image label before binding pixels.")
    return (tuple(Path(path) for _, path in named) + tuple(paths),
            tuple(labels) + tuple(f"Unlabeled attachment {index+1}" for index in range(len(paths))))


def attachment_note(labels: Sequence[str], source: bool = False) -> str:
    roles = (["edit source"] if source else []) + list(labels)
    return "\n\nAttached images in order: " + json.dumps(roles, ensure_ascii=False) if roles else ""
