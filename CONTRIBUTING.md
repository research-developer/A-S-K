# Contributing to A-S-K

Thank you for your interest in contributing!

## How to contribute

- Propose operator mappings or counterexamples with citations in issues or PRs.
- Add decoded words to `data/decoded_words.jsonl` following the JSONL schema.
- Extend `src/ask/glyphs.py` with new clusters or refine payload/operator maps.
- Improve `decode_word()` logic or add proper morphological segmentation.
- Add tests under `tests/` and ensure they pass.

## Development setup

1. Create a virtualenv and install deps:

   ```bash
   python3 -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. Run the CLI locally (without installing the package):

   ```bash
   PYTHONPATH=src python -m ask.cli decode ask
   PYTHONPATH=src python -m ask.cli decode manipulation --json-out
   ```

3. Run tests:

   ```bash
   PYTHONPATH=src python -m pytest -q
   ```

## Code style

- Keep modules small and focused.
- Prefer pure functions and typed dicts/dataclasses where helpful.
- Add docstrings and brief rationales when introducing new axioms/mappings.

## Governance

- MIT licensed. By contributing you agree to license your contributions under MIT.
- Use PRs for non-trivial changes; include rationale and references.
