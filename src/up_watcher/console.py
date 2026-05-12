from __future__ import annotations

import os
import shutil
import sys
import textwrap
from datetime import datetime
from typing import Iterable, Mapping


_COLORS = {
    "reset": "\033[0m",
    "bold": "\033[1m",
    "dim": "\033[2m",
    "red": "\033[31m",
    "green": "\033[32m",
    "yellow": "\033[33m",
    "blue": "\033[34m",
    "cyan": "\033[36m",
}


def _can_color() -> bool:
    return sys.stdout.isatty() and os.getenv("NO_COLOR") is None


def _paint(text: str, *styles: str) -> str:
    if not _can_color():
        return text
    prefix = "".join(_COLORS[style] for style in styles if style in _COLORS)
    return f"{prefix}{text}{_COLORS['reset']}" if prefix else text


def _terminal_width() -> int:
    return max(56, min(96, shutil.get_terminal_size((88, 24)).columns))


def _rule(title: str) -> str:
    title = f" {title} "
    width = _terminal_width()
    right = max(0, width - len(title))
    return f"{title}{'─' * right}"


def _timestamp() -> str:
    return datetime.now().strftime("%H:%M:%S")


def section(title: str) -> None:
    print()
    print(_paint(_rule(title), "bold", "blue"))


def line() -> None:
    print(_paint("─" * _terminal_width(), "dim"))


def _log(level: str, message: str, color: str) -> None:
    timestamp = _paint(_timestamp(), "dim")
    label = _paint(level, color, "bold")
    print(f"{timestamp} {label} {message}")


def info(message: str) -> None:
    _log("信息", message, "cyan")


def success(message: str) -> None:
    _log("成功", message, "green")


def warning(message: str) -> None:
    _log("提醒", message, "yellow")


def error(message: str) -> None:
    _log("错误", message, "red")


def command_hint(command: str) -> None:
    print(f"  {_paint('$', 'dim')} {command}")


def key_values(title: str, rows: Iterable[tuple[str, object]]) -> None:
    section(title)
    for key, value in rows:
        print(f"{_paint(key + '：', 'cyan')}{value}")
    line()


def show_video_info(video_info: Mapping[str, object]) -> None:
    key_values(
        "视频信息",
        (
            ("标题", video_info["title"]),
            ("UP 主", video_info["up_name"]),
            ("UP 主编号", video_info["up_mid"]),
            ("视频编号", video_info["aid"]),
        ),
    )


def show_watch_settings(interval: int, watch_all: bool, feishu_enabled: bool = False) -> None:
    key_values(
        "监控设置",
        (
            ("监听范围", "全部评论" if watch_all else "仅 UP 主评论"),
            ("轮询间隔", f"{interval} 秒" if interval > 5 else "智能间隔"),
            ("飞书推送", "已开启" if feishu_enabled else "未开启"),
        ),
    )


def show_comments(comments: list[dict]) -> None:
    section(f"发现 {len(comments)} 条新评论")
    width = max(24, _terminal_width() - 8)
    for index, comment in enumerate(comments, start=1):
        user = str(comment.get("uname", "未知用户"))
        ctime = str(comment.get("ctime", "未知时间"))
        message = str(comment.get("message", "")).strip() or "（空内容）"

        print(_paint(f"{index}. {user}", "green", "bold"))
        print(f"   时间：{ctime}")
        for line_text in _wrap_comment(message, width):
            print(f"   内容：{line_text}")
        if index != len(comments):
            print()
    line()


def _wrap_comment(message: str, width: int) -> list[str]:
    wrapped: list[str] = []
    for raw_line in message.splitlines() or [""]:
        wrapped.extend(
            textwrap.wrap(
                raw_line,
                width=width,
                replace_whitespace=False,
                break_long_words=False,
                break_on_hyphens=False,
            )
            or [""]
        )
    return wrapped
