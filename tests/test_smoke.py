import ctypes

import pytest

import tv_switcher
from tv_switcher import display


def test_struct_sizes_match_windows_abi():
    assert ctypes.sizeof(display.DISPLAYCONFIG_PATH_INFO) == 72
    assert ctypes.sizeof(display.DISPLAYCONFIG_MODE_INFO) == 64
    assert ctypes.sizeof(display.DISPLAYCONFIG_TARGET_DEVICE_NAME) == 420


def test_switch_order(monkeypatch, capsys):
    calls = []
    monkeypatch.setattr(display, "enable", lambda m: calls.append(("enable", m)))
    monkeypatch.setattr(display, "set_primary", lambda m: calls.append(("primary", m)))
    monkeypatch.setattr(display, "disable", lambda m: calls.append(("disable", m)))
    monkeypatch.setattr(tv_switcher.audio, "set_default_output", lambda n: n)

    tv_switcher.switch(tv_switcher.PROFILES["0"])
    a, b = tv_switcher.DISPLAY_A, tv_switcher.DISPLAY_B
    assert calls == [("enable", a), ("primary", a), ("disable", b)]

    calls.clear()
    tv_switcher.switch(tv_switcher.PROFILES["1"])
    assert calls == [("enable", b), ("primary", b)]
    assert "LG TV SSCR2" in capsys.readouterr().out


def test_rejects_bad_mode(monkeypatch):
    monkeypatch.setattr("sys.argv", ["tv-switcher", "2"])
    with pytest.raises(SystemExit):
        tv_switcher.main()


def test_audio_waits_for_device_and_reasserts(monkeypatch):
    from tv_switcher import audio

    tv = ("LG TV SSCR2 (NVIDIA)", "tv-id")
    # Device absent on first poll, then present; Windows resets the default once.
    outputs = iter([[], [tv], [tv], [tv], [tv], [tv]])
    defaults = iter([None, "other", "tv-id", "tv-id"])
    sets = []
    monkeypatch.setattr(audio, "list_outputs", lambda: next(outputs))
    monkeypatch.setattr(audio, "default_output_id", lambda: next(defaults))
    monkeypatch.setattr(audio.AudioUtilities, "SetDefaultDevice", lambda i, roles: sets.append(i))
    monkeypatch.setattr(audio.time, "sleep", lambda s: None)

    assert audio.set_default_output("LG TV SSCR2") == tv[0]
    assert sets == ["tv-id", "tv-id"]
