import time
import random
from .utils import play_audio
from datetime import datetime
from threading import Thread
from typing import Callable
from . import console
from .config import get_config_value, set_config
from .video import get_video_info, get_comments
from .im import (
    connect_feishu,
    is_feishu_connect_to_user,
    feishu_handle_new_comments
)


def _get_wait_value():
    """
    获取等待时间，根据 A 股交易时间进行动态调整。
    主要面向 A 股 UP 视频评论进行监控。
    """
    now = datetime.now()
    current_minutes = now.hour * 60 + now.minute
    
    if 9 * 60 + 20 <= current_minutes <= 9 * 60 + 40:   # 09:20 ~ 09:40
        return 20 + random.randint(0, 10)
    elif 9 * 60 + 40 < current_minutes <= 11 * 60 + 30: # 09:40 ~ 11:30
        return 40 + random.randint(0, 20)
    elif 13 * 60 <= current_minutes <= 15 * 60:         # 13:00 ~ 15:00
        return 90 + random.randint(0, 30)
    else:
        return 300


comment_pool = {}


def _show_wait_countdown(wait_time: int, total_wait_time: int) -> None:
    width = len(str(total_wait_time))
    print(f"\r下次检查倒计时：{wait_time:>{width}} 秒后检查评论\033[K", end="", flush=True)


def _clear_wait_countdown() -> None:
    print("\r\033[K", end="", flush=True)


def _wait_for_next_check(wait_time: int) -> bool:
    total_wait_time = wait_time
    while wait_time > 0:
        _show_wait_countdown(wait_time, total_wait_time)
        time.sleep(1)
        wait_time -= 1
        if get_config_value("stop"):
            _clear_wait_countdown()
            return False
    _clear_wait_countdown()
    return True


def _play_comment_alert_sound() -> None:
    def _play() -> None:
        try:
            play_audio("ring.wav")
        except Exception as exc:
            console.warning(f"声音提醒播放失败：{exc}")

    Thread(target=_play, name="comment-alert-sound", daemon=True).start()


def handle_comments(
    mid: str,
    comments,
    watch_all: bool,
    sound_enabled: bool,
    new_comments_callback: Callable | None = None,
):
    global comment_pool
    new_comments = []
    for comment in comments:
        if comment["mid"] == mid or watch_all:
            if comment["rpid"] not in comment_pool:
                comment_pool[comment["rpid"]] = comment
                new_comments.append(comment)

    if len(new_comments) > 0:
        if sound_enabled:
            _play_comment_alert_sound()
        if new_comments_callback:
            new_comments_callback(new_comments)
        console.show_comments(new_comments)
    else:
        console.info("未发现新评论")

def video_comments_watcher(bvid: str, interval: int, watch_all: bool = False, sound_enabled: bool = False) -> None:
    console.info("正在获取视频信息...")
    video_info = get_video_info(bvid)
    aid = video_info["aid"]
    up_mid = video_info["up_mid"]
    console.show_video_info(video_info)
    console.show_watch_settings(interval, watch_all, sound_enabled=sound_enabled)

    console.info("正在获取评论...")
    handle_comments(up_mid, get_comments(aid), watch_all, sound_enabled)

    set_config("stop", False)
    console.success("监控已启动，按 Ctrl+C 退出；也可以在另一个终端运行 upw stop 停止")
    while True:
        console.info("正在获取评论...")
        wait_time = interval if interval > 5 else _get_wait_value()
        if not _wait_for_next_check(wait_time):
            console.success("已收到停止指令，监控结束")
            return
        handle_comments(up_mid, get_comments(aid), watch_all, sound_enabled)


def video_comments_watcher_feishu(
    bvid: str,
    interval: int,
    watch_all: bool = False,
    sound_enabled: bool = False,
) -> None:
    console.info("正在获取视频信息...")
    video_info = get_video_info(bvid)
    aid = video_info["aid"]
    up_mid = video_info["up_mid"]
    console.show_video_info(video_info)
    console.show_watch_settings(interval, watch_all, True, sound_enabled)

    watch_info = "\n".join(
        [
            f"- 视频名称：{video_info['title']}",
            f"- UP 主：{video_info['up_name']}",
            f"- 监控间隔：{f'{interval} 秒' if interval > 5 else '智能间隔'}",
        ]
    )

    console.info("正在连接飞书机器人...")
    if not connect_feishu(watch_info):
        return

    console.info("正在等待用户向飞书机器人发送信息...")
    while not is_feishu_connect_to_user():
        time.sleep(1)

    console.info("正在获取评论...")
    handle_comments(up_mid, get_comments(aid), watch_all, sound_enabled, feishu_handle_new_comments)

    set_config("stop", False)
    console.success("监控已启动，按 Ctrl+C 退出；也可以在另一个终端运行 upw stop 停止")
    while True:
        wait_time = interval if interval > 5 else _get_wait_value()
        if not _wait_for_next_check(wait_time):
            console.success("已收到停止指令，监控结束")
            return
        handle_comments(up_mid, get_comments(aid), watch_all, sound_enabled, feishu_handle_new_comments)
