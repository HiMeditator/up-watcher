import builtins

import pytest

from up_watcher import watcher
from up_watcher.utils import audio


def test_handle_comments_compares_mid_as_string(monkeypatch):
    watcher.comment_pool = {}
    shown_comments = []

    monkeypatch.setattr(watcher.console, "show_comments", shown_comments.append)
    monkeypatch.setattr(watcher.console, "info", lambda message: None)

    watcher.handle_comments(
        "123",
        [{"rpid": 1, "mid": 123, "uname": "Alice", "ctime": "now", "message": "hi"}],
        watch_all=False,
        sound_enabled=False,
    )

    assert shown_comments[0][0]["mid"] == 123


def test_load_feishu_support_has_actionable_error_when_extra_missing(monkeypatch):
    real_import = builtins.__import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "im" and level == 1:
            raise ModuleNotFoundError("No module named 'lark_oapi'", name="lark_oapi")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    with pytest.raises(RuntimeError, match=r"up-watcher\[feishu\]"):
        watcher._load_feishu_support()


def test_play_audio_has_actionable_error_when_sound_extra_missing(monkeypatch):
    real_import = builtins.__import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "simpleaudio":
            raise ImportError("No module named 'simpleaudio'")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(audio.sys, "platform", "linux")
    monkeypatch.setattr(builtins, "__import__", fake_import)

    with pytest.raises(RuntimeError, match=r"up-watcher\[sound\]"):
        audio.play_audio("ring.wav")
