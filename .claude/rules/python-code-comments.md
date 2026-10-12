---
paths:
  - "**/*.py"
---

# Python code comment rules

- Do not write comments. Code, names, and structure carry the "what"; when an explanation feels necessary, rewrite the code instead of annotating it.
- Allowed mechanical exceptions are docstrings on public modules, classes, and functions (not on `_private` names), tool directives with the reason they require (`# noqa: <code>`, `# type: ignore[<code>]`, `# pragma: no cover`, `# fmt: off`/`# fmt: on`), shebangs, PEP 723 `# /// script` blocks, and license or generated-file headers.
- A minimal rationale is also allowed where code intentionally departs from a language or project convention and a future maintainer could otherwise "fix" it and reintroduce a defect. Do not use this exception for ordinary implementation choices.
- In CAD sources, two more comments are allowed:
  - A physical reference that names and types cannot express, such as which corner or face a coordinate frame starts from.
  - A `TODO(<id>)` marker on a placeholder value awaiting measurement, such as `TODO(donor)`.
- Do not annotate units. Lengths are in millimeters by default; put any other unit in the name, such as `tilt_deg`.
- Rationale that does not fit those exceptions goes in the commit message, the PR description, or `docs/` — never in the source.
- This governs the lines you write or change. Do not strip existing comments as drive-by cleanup; drop one only when the code it describes is being rewritten anyway.
- Apply the same rule to code samples and diffs you put in issues, PRs, and plan documents: write the example the way the code should actually land.
