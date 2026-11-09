# tv-switcher

Windows CLI that switches between the desk monitor and the TV with one command, changing both
the primary display and the default audio output.

## Requirements
- Windows (uses the CCD display API and Core Audio via [pycaw](https://github.com/AndreMiras/pycaw))
- Python 3.14+ and [uv](https://docs.astral.sh/uv/)

## Setup
```
uv sync
```

## Usage
```
uv run tv-switcher 0        # desk monitor
uv run tv-switcher 1        # TV
uv run tv-switcher status   # list displays and playback devices
```

| Mode | Primary display | Also does | Audio output |
|------|-----------------|-----------|--------------|
| `0`  | LG ULTRAGEAR 3440x1440 (`GSM774B`) | Turns off the TV | `Playback 1/2` |
| `1`  | LG TV SSCR2 3840x2160 (`GSM82CD`) | Leaves the desk monitor on | `LG TV SSCR2` |

The third monitor (`GSM5BB2`, 1920x1080) is never touched by either mode.

`status` prints each display's state (`primary`, `active` or `off`), name, resolution and device
path, followed by the names of all playback devices.

## Configuration
Profiles live in `PROFILES` in `src/tv_switcher/__init__.py`:

- **Displays** are matched by a substring of the device path (the EDID hardware ID such as
  `GSM774B`), not by friendly name, because two monitors are both called "LG ULTRAGEAR".
- **Audio** devices are matched by the start of their friendly name.

Run `uv run tv-switcher status` to find the IDs and names for your own hardware.

## Development
```
uv run pytest           # tests
uv run ruff check .     # lint (add --fix to auto-fix)
uv run ruff format .    # format
```
