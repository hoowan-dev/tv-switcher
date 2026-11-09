"""Default audio output selection via pycaw (IPolicyConfig)."""

from __future__ import annotations

import time

from pycaw.constants import DEVICE_STATE, EDataFlow, ERole
from pycaw.utils import AudioUtilities

ALL_ROLES = [ERole.eConsole, ERole.eMultimedia, ERole.eCommunications]
POLL_INTERVAL = 0.5
STABLE_CHECKS = 2  # default must stick for this many consecutive polls


class AudioError(RuntimeError):
    pass


def list_outputs() -> list[tuple[str, str]]:
    """Return (friendly_name, endpoint_id) for every active playback device."""
    devices = AudioUtilities.GetAllDevices(EDataFlow.eRender.value, DEVICE_STATE.ACTIVE.value)
    return [(d.FriendlyName or "", d.id) for d in devices]


def default_output_id() -> str | None:
    try:
        dev = AudioUtilities.GetDeviceEnumerator().GetDefaultAudioEndpoint(
            EDataFlow.eRender.value, ERole.eMultimedia.value
        )
        return dev.GetId()
    except OSError:  # no default device (e.g. mid-reconfiguration)
        return None


def _find(name_prefix: str) -> tuple[str, str] | None:
    for name, dev_id in list_outputs():
        if name.lower().startswith(name_prefix.lower()):
            return name, dev_id
    return None


def set_default_output(name_prefix: str, timeout: float = 15.0) -> str:
    """Make the playback device whose name starts with ``name_prefix`` the default.

    After a display change, HDMI audio endpoints can take a few seconds to appear, and
    Windows may reassign the default while they settle. So wait for the device, set it,
    and keep re-asserting until it sticks.
    """
    deadline = time.monotonic() + timeout
    stable = 0
    found = None
    while time.monotonic() < deadline:
        found = _find(name_prefix)
        if found:
            name, dev_id = found
            if default_output_id() == dev_id:
                stable += 1
                if stable >= STABLE_CHECKS:
                    return name
            else:
                stable = 0
                AudioUtilities.SetDefaultDevice(dev_id, roles=ALL_ROLES)
        time.sleep(POLL_INTERVAL)

    if found:
        raise AudioError(f"{found[0]!r} did not stay the default output within {timeout:.0f}s")
    available = ", ".join(n for n, _ in list_outputs()) or "none"
    raise AudioError(
        f"No active playback device named {name_prefix!r} after {timeout:.0f}s "
        f"(available: {available})"
    )
