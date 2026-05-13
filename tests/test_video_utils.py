import pytest

from up_watcher.video import utils as video_utils


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload
        self.raise_for_status_called = False

    def raise_for_status(self):
        self.raise_for_status_called = True

    def json(self):
        return self.payload


class FakeSession:
    def __init__(self, payload):
        self.headers = {}
        self.response = FakeResponse(payload)
        self.calls = []

    def get(self, url, params, timeout):
        self.calls.append({"url": url, "params": params, "timeout": timeout})
        return self.response


def install_fake_session(monkeypatch, payload):
    sessions = []

    def make_session():
        session = FakeSession(payload)
        sessions.append(session)
        return session

    monkeypatch.setattr(video_utils.requests, "Session", make_session)
    return sessions


def test_get_video_info_uses_timeout_and_normalizes_mid(monkeypatch):
    sessions = install_fake_session(
        monkeypatch,
        {
            "code": 0,
            "data": {
                "aid": 123,
                "title": "测试视频",
                "owner": {"name": "UP 主", "mid": 456},
            },
        },
    )

    result = video_utils.get_video_info("BV123", timeout=3)

    assert result == {
        "aid": 123,
        "title": "测试视频",
        "up_name": "UP 主",
        "up_mid": "456",
    }
    assert sessions[0].calls == [
        {
            "url": "https://api.bilibili.com/x/web-interface/view",
            "params": {"bvid": "BV123"},
            "timeout": 3,
        }
    ]


def test_get_video_info_raises_on_api_error(monkeypatch):
    install_fake_session(monkeypatch, {"code": -400, "message": "bad request"})

    with pytest.raises(RuntimeError, match="视频信息接口返回错误"):
        video_utils.get_video_info("bad-bvid")


def test_get_video_replies_uses_cookie_timeout_and_extra_params(monkeypatch):
    sessions = install_fake_session(
        monkeypatch,
        {"code": 0, "data": {"page": {"num": 1}, "replies": []}},
    )

    result = video_utils.get_video_replies(
        123,
        cookie="SESSDATA=abc",
        kwargs={"ps": 10},
        timeout=7,
    )

    assert result == {"page": {"num": 1}, "replies": []}
    assert sessions[0].headers["Cookie"] == "SESSDATA=abc"
    assert sessions[0].calls[0]["params"] == {
        "oid": 123,
        "type": 1,
        "sort": 0,
        "pn": 1,
        "ps": 10,
    }
    assert sessions[0].calls[0]["timeout"] == 7


def test_get_video_replies_without_cookie_shows_upw_hint(monkeypatch):
    install_fake_session(monkeypatch, {"code": 0, "data": {"page": {}, "replies": []}})
    hints = []
    warnings = []

    monkeypatch.setattr(video_utils, "get_config_value", lambda key: None)
    monkeypatch.setattr(video_utils.console, "warning", warnings.append)
    monkeypatch.setattr(video_utils.console, "command_hint", hints.append)

    video_utils.get_video_replies(123)

    assert warnings
    assert hints == ['upw set cookie "your_bilibili_cookie"']


def test_replies_extractor_normalizes_comment_mid_to_string():
    result = video_utils.replies_extractor(
        {
            "page": {"num": 1},
            "replies": [
                {
                    "rpid": 1,
                    "member": {"uname": "Alice", "mid": 456},
                    "ctime": 0,
                    "content": {"message": "hello"},
                }
            ],
        }
    )

    assert result["comments"][0]["mid"] == "456"
    assert result["comments"][0]["message"] == "hello"


def test_replies_extractor_handles_empty_replies():
    assert video_utils.replies_extractor({"page": {"num": 1}, "replies": None}) == {
        "page": {"num": 1},
        "comments": [],
    }
