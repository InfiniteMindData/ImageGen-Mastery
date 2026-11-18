"""Compile user-supplied visual directions into a deterministic text prompt."""


def _object(value, path, required, optional=()):
    if not isinstance(value, dict):
        raise ValueError(f"{path} must be an object")
    for key in value:
        if key not in required and key not in optional:
            raise ValueError(f"Unknown field {path}.{key}")
    for key in required:
        if key not in value:
            raise ValueError(f"{path}.{key} is required")


def _text(value, path):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{path} must be a nonblank string")
    return value


def _items(value, path):
    if not isinstance(value, list):
        raise ValueError(f"{path} must be a list")
    return enumerate(value)


def _reference_notes(value):
    notes = []
    for index, ref in _items(value, "references"):
        path = f"references[{index}]"
        _object(ref, path, ("image", "anchors"))
        source = _text(ref["image"], f"{path}.image")
        lines = [f"Reference notes from {source}"]
        for number, anchor in _items(ref["anchors"], f"{path}.anchors"):
            field = f"{path}.anchors[{number}]"
            _object(anchor, field, ("aspect", "detail"))
            aspect = _text(anchor["aspect"], f"{field}.aspect")
            detail = _text(anchor["detail"], f"{field}.detail")
            lines.append(f"- {aspect} — {detail}")
        if not ref["anchors"]:
            raise ValueError(f"{path}.anchors must contain a described visual feature")
        notes.append("\n".join(lines))
    return notes


def _revision_notes(value):
    notes = []
    for index, revision in _items(value, "revisions"):
        path = f"revisions[{index}]"
        _object(revision, path, ("observed", "change"))
        observed = _text(revision["observed"], f"{path}.observed")
        change = _text(revision["change"], f"{path}.change")
        notes.append(f"Observed issue\n{observed}\nRequested correction\n{change}")
    if notes:
        notes.insert(0, "Apply these corrections while preserving the rest of the brief.")
    return notes


def optimize(brief: dict) -> str:
    """Render a brief without inferring details or loading its named references.

    Raise ValueError with the field location when the brief is malformed.
    """
    directions = ("composition", "style", "lighting")
    optional = (*directions, "constraints", "avoid", "references", "revisions", "locked_attributes", "creative_options")
    _object(brief, "brief", ("intent",), optional)
    sections = [_text(brief["intent"], "intent")]
    for key in directions:
        if key in brief:
            sections.append(f"{key.capitalize()}\n{_text(brief[key], key)}")
    sections.extend(_reference_notes(brief.get("references", [])))
    for key, title in (("constraints", "Requirements"), ("avoid", "Exclude these elements"),
                       ("locked_attributes", "Preserve these locked attributes"),
                       ("creative_options", "Optional artistic choices (use only if they serve the requirements)")):
        lines = [
            "- " + _text(item, f"{key}[{index}]")
            for index, item in _items(brief.get(key, []), key)
        ]
        if lines:
            sections.append("\n".join([title, *lines]))
    sections.extend(_revision_notes(brief.get("revisions", [])))
    return "\n\n".join(sections)


def review_requirements(brief: dict) -> list[str]:
    # Bind every defect to an original instruction; model output cannot add an edit goal.
    items = [brief["intent"]]
    for key in ("style", "lighting", "composition"):
        if key in brief:
            items.append(brief[key])
    items.extend(brief.get("constraints", []))
    items.extend("Exclude: " + item for item in brief.get("avoid", []))
    for ref in brief.get("references", []):
        for anchor in ref["anchors"]:
            items.append(f'{ref["image"]}: {anchor["aspect"]} — {anchor["detail"]}')
    items.extend(item["change"] for item in brief.get("revisions", []))
    return items
