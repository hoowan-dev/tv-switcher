"""Display topology control via the Windows CCD API (QueryDisplayConfig / SetDisplayConfig)."""

from __future__ import annotations

import ctypes
from ctypes import wintypes
from dataclasses import dataclass

user32 = ctypes.WinDLL("user32")

# QueryDisplayConfig flags
QDC_ALL_PATHS = 0x1
QDC_ONLY_ACTIVE_PATHS = 0x2

# SetDisplayConfig flags
SDC_USE_SUPPLIED_DISPLAY_CONFIG = 0x20
SDC_APPLY = 0x80
SDC_SAVE_TO_DATABASE = 0x200
SDC_ALLOW_CHANGES = 0x400

DISPLAYCONFIG_PATH_ACTIVE = 0x1
DISPLAYCONFIG_PATH_MODE_IDX_INVALID = 0xFFFFFFFF
DISPLAYCONFIG_MODE_INFO_TYPE_SOURCE = 1

DISPLAYCONFIG_DEVICE_INFO_GET_SOURCE_NAME = 1
DISPLAYCONFIG_DEVICE_INFO_GET_TARGET_NAME = 2

ERROR_SUCCESS = 0
ERROR_INSUFFICIENT_BUFFER = 122


class LUID(ctypes.Structure):
    _fields_ = [("LowPart", wintypes.DWORD), ("HighPart", wintypes.LONG)]

    def key(self) -> tuple[int, int]:
        return (self.LowPart, self.HighPart)


class DISPLAYCONFIG_RATIONAL(ctypes.Structure):
    _fields_ = [("Numerator", ctypes.c_uint32), ("Denominator", ctypes.c_uint32)]


class DISPLAYCONFIG_PATH_SOURCE_INFO(ctypes.Structure):
    _fields_ = [
        ("adapterId", LUID),
        ("id", ctypes.c_uint32),
        ("modeInfoIdx", ctypes.c_uint32),
        ("statusFlags", ctypes.c_uint32),
    ]


class DISPLAYCONFIG_PATH_TARGET_INFO(ctypes.Structure):
    _fields_ = [
        ("adapterId", LUID),
        ("id", ctypes.c_uint32),
        ("modeInfoIdx", ctypes.c_uint32),
        ("outputTechnology", ctypes.c_uint32),
        ("rotation", ctypes.c_uint32),
        ("scaling", ctypes.c_uint32),
        ("refreshRate", DISPLAYCONFIG_RATIONAL),
        ("scanLineOrdering", ctypes.c_uint32),
        ("targetAvailable", wintypes.BOOL),
        ("statusFlags", ctypes.c_uint32),
    ]


class DISPLAYCONFIG_PATH_INFO(ctypes.Structure):
    _fields_ = [
        ("sourceInfo", DISPLAYCONFIG_PATH_SOURCE_INFO),
        ("targetInfo", DISPLAYCONFIG_PATH_TARGET_INFO),
        ("flags", ctypes.c_uint32),
    ]


class DISPLAYCONFIG_2DREGION(ctypes.Structure):
    _fields_ = [("cx", ctypes.c_uint32), ("cy", ctypes.c_uint32)]


class DISPLAYCONFIG_VIDEO_SIGNAL_INFO(ctypes.Structure):
    _fields_ = [
        ("pixelRate", ctypes.c_uint64),
        ("hSyncFreq", DISPLAYCONFIG_RATIONAL),
        ("vSyncFreq", DISPLAYCONFIG_RATIONAL),
        ("activeSize", DISPLAYCONFIG_2DREGION),
        ("totalSize", DISPLAYCONFIG_2DREGION),
        ("videoStandard", ctypes.c_uint32),
        ("scanLineOrdering", ctypes.c_uint32),
    ]


class DISPLAYCONFIG_TARGET_MODE(ctypes.Structure):
    _fields_ = [("targetVideoSignalInfo", DISPLAYCONFIG_VIDEO_SIGNAL_INFO)]


class DISPLAYCONFIG_SOURCE_MODE(ctypes.Structure):
    _fields_ = [
        ("width", ctypes.c_uint32),
        ("height", ctypes.c_uint32),
        ("pixelFormat", ctypes.c_uint32),
        ("position", wintypes.POINTL),
    ]


class DISPLAYCONFIG_DESKTOP_IMAGE_INFO(ctypes.Structure):
    _fields_ = [
        ("PathSourceSize", wintypes.POINTL),
        ("DesktopImageRegion", wintypes.RECTL),
        ("DesktopImageClip", wintypes.RECTL),
    ]


class _ModeUnion(ctypes.Union):
    _fields_ = [
        ("targetMode", DISPLAYCONFIG_TARGET_MODE),
        ("sourceMode", DISPLAYCONFIG_SOURCE_MODE),
        ("desktopImageInfo", DISPLAYCONFIG_DESKTOP_IMAGE_INFO),
    ]


class DISPLAYCONFIG_MODE_INFO(ctypes.Structure):
    _anonymous_ = ("u",)
    _fields_ = [
        ("infoType", ctypes.c_uint32),
        ("id", ctypes.c_uint32),
        ("adapterId", LUID),
        ("u", _ModeUnion),
    ]


class DISPLAYCONFIG_DEVICE_INFO_HEADER(ctypes.Structure):
    _fields_ = [
        ("type", ctypes.c_uint32),
        ("size", ctypes.c_uint32),
        ("adapterId", LUID),
        ("id", ctypes.c_uint32),
    ]


class DISPLAYCONFIG_TARGET_DEVICE_NAME(ctypes.Structure):
    _fields_ = [
        ("header", DISPLAYCONFIG_DEVICE_INFO_HEADER),
        ("flags", ctypes.c_uint32),
        ("outputTechnology", ctypes.c_uint32),
        ("edidManufactureId", ctypes.c_uint16),
        ("edidProductCodeId", ctypes.c_uint16),
        ("connectorInstance", ctypes.c_uint32),
        ("monitorFriendlyDeviceName", ctypes.c_wchar * 64),
        ("monitorDevicePath", ctypes.c_wchar * 128),
    ]


class DISPLAYCONFIG_SOURCE_DEVICE_NAME(ctypes.Structure):
    _fields_ = [
        ("header", DISPLAYCONFIG_DEVICE_INFO_HEADER),
        ("viewGdiDeviceName", ctypes.c_wchar * 32),
    ]


user32.GetDisplayConfigBufferSizes.argtypes = [
    ctypes.c_uint32,
    ctypes.POINTER(ctypes.c_uint32),
    ctypes.POINTER(ctypes.c_uint32),
]
user32.GetDisplayConfigBufferSizes.restype = wintypes.LONG
user32.QueryDisplayConfig.argtypes = [
    ctypes.c_uint32,
    ctypes.POINTER(ctypes.c_uint32),
    ctypes.POINTER(DISPLAYCONFIG_PATH_INFO),
    ctypes.POINTER(ctypes.c_uint32),
    ctypes.POINTER(DISPLAYCONFIG_MODE_INFO),
    ctypes.c_void_p,
]
user32.QueryDisplayConfig.restype = wintypes.LONG
user32.SetDisplayConfig.argtypes = [
    ctypes.c_uint32,
    ctypes.POINTER(DISPLAYCONFIG_PATH_INFO),
    ctypes.c_uint32,
    ctypes.POINTER(DISPLAYCONFIG_MODE_INFO),
    ctypes.c_uint32,
]
user32.SetDisplayConfig.restype = wintypes.LONG
user32.DisplayConfigGetDeviceInfo.argtypes = [ctypes.POINTER(DISPLAYCONFIG_DEVICE_INFO_HEADER)]
user32.DisplayConfigGetDeviceInfo.restype = wintypes.LONG


class DisplayError(RuntimeError):
    pass


def _check(rc: int, what: str) -> None:
    if rc != ERROR_SUCCESS:
        raise DisplayError(f"{what} failed: {ctypes.FormatError(rc).strip()} (code {rc})")


@dataclass
class Config:
    paths: list[DISPLAYCONFIG_PATH_INFO]
    modes: list[DISPLAYCONFIG_MODE_INFO]


def query(flags: int) -> Config:
    while True:
        n_paths, n_modes = ctypes.c_uint32(), ctypes.c_uint32()
        _check(
            user32.GetDisplayConfigBufferSizes(flags, n_paths, n_modes),
            "GetDisplayConfigBufferSizes",
        )
        paths = (DISPLAYCONFIG_PATH_INFO * n_paths.value)()
        modes = (DISPLAYCONFIG_MODE_INFO * n_modes.value)()
        rc = user32.QueryDisplayConfig(flags, n_paths, paths, n_modes, modes, None)
        if rc == ERROR_INSUFFICIENT_BUFFER:  # topology changed between calls; retry
            continue
        _check(rc, "QueryDisplayConfig")
        return Config(list(paths[: n_paths.value]), list(modes[: n_modes.value]))


def apply(paths: list[DISPLAYCONFIG_PATH_INFO], modes: list[DISPLAYCONFIG_MODE_INFO]) -> None:
    path_arr = (DISPLAYCONFIG_PATH_INFO * len(paths))(*paths)
    mode_arr = (DISPLAYCONFIG_MODE_INFO * len(modes))(*modes)
    flags = SDC_APPLY | SDC_USE_SUPPLIED_DISPLAY_CONFIG | SDC_SAVE_TO_DATABASE | SDC_ALLOW_CHANGES
    _check(
        user32.SetDisplayConfig(len(paths), path_arr, len(modes), mode_arr, flags),
        "SetDisplayConfig",
    )


def target_name(path: DISPLAYCONFIG_PATH_INFO) -> DISPLAYCONFIG_TARGET_DEVICE_NAME:
    info = DISPLAYCONFIG_TARGET_DEVICE_NAME()
    info.header.type = DISPLAYCONFIG_DEVICE_INFO_GET_TARGET_NAME
    info.header.size = ctypes.sizeof(info)
    info.header.adapterId = path.targetInfo.adapterId
    info.header.id = path.targetInfo.id
    _check(user32.DisplayConfigGetDeviceInfo(info.header), "DisplayConfigGetDeviceInfo(target)")
    return info


def source_gdi_name(path: DISPLAYCONFIG_PATH_INFO) -> str:
    info = DISPLAYCONFIG_SOURCE_DEVICE_NAME()
    info.header.type = DISPLAYCONFIG_DEVICE_INFO_GET_SOURCE_NAME
    info.header.size = ctypes.sizeof(info)
    info.header.adapterId = path.sourceInfo.adapterId
    info.header.id = path.sourceInfo.id
    _check(user32.DisplayConfigGetDeviceInfo(info.header), "DisplayConfigGetDeviceInfo(source)")
    return info.viewGdiDeviceName


def _target_key(path: DISPLAYCONFIG_PATH_INFO) -> tuple:
    return (path.targetInfo.adapterId.key(), path.targetInfo.id)


def _source_key(path: DISPLAYCONFIG_PATH_INFO) -> tuple:
    return (path.sourceInfo.adapterId.key(), path.sourceInfo.id)


def _is_active(path: DISPLAYCONFIG_PATH_INFO) -> bool:
    return bool(path.flags & DISPLAYCONFIG_PATH_ACTIVE)


def _matches(path: DISPLAYCONFIG_PATH_INFO, monitor_id: str) -> bool:
    return monitor_id.lower() in target_name(path).monitorDevicePath.lower()


def _active_paths_for(cfg: Config, monitor_id: str) -> list[DISPLAYCONFIG_PATH_INFO]:
    return [p for p in cfg.paths if _is_active(p) and _matches(p, monitor_id)]


def list_displays() -> list[dict]:
    """Describe every connected monitor, active or not."""
    cfg = query(QDC_ALL_PATHS)
    seen: dict[tuple, dict] = {}
    for p in cfg.paths:
        if not p.targetInfo.targetAvailable:
            continue
        key = _target_key(p)
        if key in seen and not _is_active(p):
            continue
        name = target_name(p)
        entry = {
            "name": name.monitorFriendlyDeviceName,
            "path": name.monitorDevicePath,
            "active": _is_active(p),
            "gdi": None,
            "size": None,
            "position": None,
        }
        if _is_active(p) and p.sourceInfo.modeInfoIdx != DISPLAYCONFIG_PATH_MODE_IDX_INVALID:
            sm = cfg.modes[p.sourceInfo.modeInfoIdx].sourceMode
            entry.update(
                gdi=source_gdi_name(p),
                size=(sm.width, sm.height),
                position=(sm.position.x, sm.position.y),
            )
        seen[key] = entry
    return list(seen.values())


def enable(monitor_id: str) -> None:
    """Activate the monitor if it is connected but currently disabled."""
    cfg = query(QDC_ALL_PATHS)
    active = [p for p in cfg.paths if _is_active(p)]
    if any(_matches(p, monitor_id) for p in active):
        return
    used_sources = {_source_key(p) for p in active}
    for p in cfg.paths:
        if (
            not _is_active(p)
            and p.targetInfo.targetAvailable
            and _source_key(p) not in used_sources
            and _matches(p, monitor_id)
        ):
            p.flags |= DISPLAYCONFIG_PATH_ACTIVE
            # Let Windows pick the mode (it restores the last-used one from its database).
            p.sourceInfo.modeInfoIdx = DISPLAYCONFIG_PATH_MODE_IDX_INVALID
            p.targetInfo.modeInfoIdx = DISPLAYCONFIG_PATH_MODE_IDX_INVALID
            apply(active + [p], cfg.modes)
            return
    raise DisplayError(f"No connected display matching {monitor_id!r} could be enabled")


def disable(monitor_id: str) -> None:
    """Deactivate the monitor, leaving all other displays as they are."""
    cfg = query(QDC_ONLY_ACTIVE_PATHS)
    keep = [p for p in cfg.paths if not _matches(p, monitor_id)]
    if len(keep) == len(cfg.paths):
        return
    if not keep:
        raise DisplayError("Refusing to disable the only active display")
    apply(keep, cfg.modes)


def set_primary(monitor_id: str) -> None:
    """Make the monitor primary by moving its desktop origin to (0, 0)."""
    cfg = query(QDC_ONLY_ACTIVE_PATHS)
    matches = _active_paths_for(cfg, monitor_id)
    if not matches:
        raise DisplayError(f"Display matching {monitor_id!r} is not active")
    src = cfg.modes[matches[0].sourceInfo.modeInfoIdx].sourceMode
    dx, dy = src.position.x, src.position.y
    if dx == 0 and dy == 0:
        return
    for m in cfg.modes:
        if m.infoType == DISPLAYCONFIG_MODE_INFO_TYPE_SOURCE:
            m.sourceMode.position.x -= dx
            m.sourceMode.position.y -= dy
    apply(cfg.paths, cfg.modes)
