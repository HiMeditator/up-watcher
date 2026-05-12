import time
import random
from datetime import datetime
from .config import get_config_value, set_config
from .video import get_video_info, get_comments

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


def handle_comments(mid: str, comments, watch_all: bool):
    new_comments = []
    for comment in comments:
        if comment["mid"] == mid or watch_all:
            if comment["rpid"] not in comment_pool:
                comment_pool[comment["rpid"]] = comment
                new_comments.append(comment)

    print(f"New comments: {len(new_comments)}")
    for comment in new_comments:
        print(f"{comment['uname']}: {comment['message']}")


def video_comments_watcher(bvid: str, interval: int, watch_all: bool = False) -> None:
    print(f"Fetching video info...")
    video_info = get_video_info(bvid)
    aid = video_info["aid"]
    up_mid = video_info["up_mid"]
    print(f"Title: {video_info['title']}")
    print(f"UP Name: {video_info['up_name']}")
    print(f"UP MID: {video_info['up_mid']}")
    print(f"AID: {video_info['aid']}")

    print("\nFetching comments...")
    handle_comments(up_mid, get_comments(aid), watch_all)

    set_config("stop", False)
    while True:
        wait_time = interval if interval > 5 else _get_wait_value()
        while wait_time > 0:
            time.sleep(1)
            wait_time -= 1
            if get_config_value("stop"):
                return
        handle_comments(up_mid, get_comments(aid), watch_all)
