"""Switch between the desk monitor (A) and the TV (B)."""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass

from tv_switcher import audio, display


@dataclass(frozen=True)
class Profile:
    label: str
    primary: str  # substring of the monitor's device path (EDID hardware ID)
    audio: str  # prefix of the playback device's friendly name
    disable: tuple[str, ...] = ()


DISPLAY_A = "GSM774B"  # LG ULTRAGEAR 3440x1440
DISPLAY_B = "GSM82CD"  # LG TV SSCR2 3840x2160

PROFILES = {
    "0": Profile("A (3440x1440 monitor)", DISPLAY_A, "Playback 1/2", disable=(DISPLAY_B,)),
    "1": Profile("B (LG TV)", DISPLAY_B, "LG TV SSCR2"),
}


def switch(profile: Profile) -> None:
    display.enable(profile.primary)
    display.set_primary(profile.primary)  # before disabling, so we never disable the primary
    for monitor_id in profile.disable:
        display.disable(monitor_id)
    name = audio.set_default_output(profile.audio)
    print(f"Switched to {profile.label}; audio -> {name}")


def show_status() -> None:
    print("Displays:")
    for d in display.list_displays():
        state = "primary" if d["position"] == (0, 0) else "active" if d["active"] else "off"
        size = "x".join(map(str, d["size"])) if d["size"] else "-"
        print(f"  [{state:7}] {d['name']:<16} {size:<10} {d['path']}")
    print("Playback devices:")
    for name, _ in audio.list_outputs():
        print(f"  {name}")


def main() -> None:
    parser = argparse.ArgumentParser(prog="tv-switcher", description=__doc__)
    parser.add_argument(
        "mode",
        choices=[*PROFILES, "status"],
        help="0 = display A + Playback 1/2, 1 = display B (TV) + TV audio, status = show devices",
    )
    args = parser.parse_args()
    try:
        if args.mode == "status":
            show_status()
        else:
            switch(PROFILES[args.mode])
    except (display.DisplayError, audio.AudioError) as e:
        print(f"tv-switcher: {e}", file=sys.stderr)
        sys.exit(1)
