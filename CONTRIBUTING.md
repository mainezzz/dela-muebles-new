# Contributing

## Workflow
1. Create a branch from `main`.
2. Make one focused change.
3. Run tests.
4. Update docs when behavior changes.
5. Open a pull request.

## Setup
```bash
python -m venv .venv
. .venv/bin/activate
pip install -e .[desktop,build,dev]
pytest
```

## Coding rules
- Keep domain logic out of Blender scripts.
- Keep the request model as the single source of truth.
- Add tests for solver, validation, or manufacturing changes.
- Do not add hardcoded variant scripts back into the main engine.
