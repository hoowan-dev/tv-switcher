# tv-switcher

Python 3.14 package managed with **uv** (src layout: `src/tv_switcher/`, tests in `tests/`).

## Commands
- Install/sync deps: `uv sync`
- Run the CLI: `uv run tv-switcher`
- Tests: `uv run pytest`
- Lint: `uv run ruff check .` (auto-fix: `--fix`)
- Format: `uv run ruff format .`
- Add a dependency: `uv add <pkg>` (dev: `uv add --dev <pkg>`)

## Conventions
- Always use `uv run` / `uv add`; never pip-install into the venv directly.
- Run tests and ruff before committing.
- Personal overrides go in `.claude/settings.local.json` and `CLAUDE.local.md` (gitignored).
