# Docscriptor Working Notes

This file is the shared memory for ongoing work on this repository. Keep it readable for the project owner, future Codex sessions, and other LLMs.

## Operating Rule

- Continue updating this file as the project evolves. Record design philosophy, API direction, compatibility rules, and decisions that future work should remember.
- Prefer explicit, author-friendly APIs over hidden magic. Docscriptor should feel like writing a document in Python, not like configuring a renderer.
- Keep one source document renderable to DOCX, PDF, and HTML. New components should define behavior for all supported renderers or clearly document limitations.
- Preserve existing examples and tests unless a user explicitly asks to change the public behavior.
- When adding a feature, update tests and examples enough that another contributor can see the intended usage.

## Current Direction

- The project builds structured documents from Python objects and exports them to DOCX, PDF, and HTML.
- Journal-style and usage-guide examples are important living specifications. They should stay realistic and readable.
- Cross-renderer consistency matters more than perfect renderer-specific fidelity.

## Active Work Memory

- Keep this shared note file and include the instruction to keep updating it.
- Keep active task details in commit messages, tests, examples, and PR notes rather than preserving every short-lived implementation idea here.

## API Evolution Notes

- Backward compatibility does not need to be preserved unless the user gives a specific compatibility guide or constraint.
- This project is still in an API-shaping stage. Prefer clear, explicit, maintainable APIs over carrying old names by default.
- Prefer document-level defaults through `DocumentSettings` when a setting should apply consistently across renderers.
- Use `Sheet` for short fixed-layout form pages such as certificates and cover inserts. It should remain a normal block inside `Document`, not a competing document root or a requirement for ordinary flowing documents. Keep fixed-sheet growth incremental: positioned text, images, simple shapes, and explicit layer ordering before heavier slide-like behavior.
- Release versioning rule: bump the minor version when backward compatibility is not guaranteed; bump only the patch version when backward compatibility is preserved.

## Local Environment Notes

- This project requires Python 3.14. On this Windows machine, use `py -3.14 ...`.
- `pytest` may not be on PATH. Prefer `py -3.14 -m pytest ...` for test commands.
