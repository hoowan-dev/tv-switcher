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

## Architecture
- `display.py`: ctypes wrapper over the Windows CCD API (QueryDisplayConfig/SetDisplayConfig).
  Monitors are matched by hardware ID in the device path (e.g. `GSM774B`), not friendly name,
  because two monitors share the name "LG ULTRAGEAR".
- `audio.py`: default playback device via pycaw's IPolicyConfig wrapper, matched by name prefix.
- `__init__.py`: `PROFILES` maps CLI modes to display/audio targets. `uv run tv-switcher status`
  prints current device IDs/names.
- A third monitor (GSM5BB2, 1920x1080) is intentionally left untouched by both profiles.
