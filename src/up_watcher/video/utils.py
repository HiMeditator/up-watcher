import requests
import datetime
from .. import console
from ..config import get_config_value


def get_video_info(bvid: str):
    """
    基于 Bilibili 视频的 BV 号获取视频关键信息，格式如下：

    ```
    {
        "aid": "视频 AID",
        "title": "视频标题",
        "up_name": "UP 名字",
        "up_mid": "UP ID"
    }
    ```
    """
    session = requests.Session()
    header_args = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://www.bilibili.com",
    }
    session.headers.update(header_args)

    url = "https://api.bilibili.com/x/web-interface/view"
    r = session.get(url, params={"bvid": bvid})
    r.raise_for_status()
    data = r.json()["data"]

    return {
        "aid": data["aid"],
        "title": data["title"],
        "up_name": data["owner"]["name"],
        "up_mid": data["owner"]["mid"],
    }


def get_video_replies(aid: int, cookie: str | None = None, kwargs: dict | None = None):
    """
    根据视频 AID 获取最新一批评论信息
    """
    session = requests.Session()

    header_args = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://www.bilibili.com",
    }
    if cookie is None: cookie = get_config_value("cookie")
    if cookie: header_args["Cookie"] = cookie
    else: console.warning("未找到 Cookie，获取评论可能失败或结果不完整")
    session.headers.update(header_args)
    url = "https://api.bilibili.com/x/v2/reply"
    
    request_params = {
        "oid": aid,
        "type": 1,
        "sort": 0,
        "pn": 1,
        # "ps": 20,
    }
    if kwargs is not None:
        request_params.update(kwargs)

    r = session.get(url, params=request_params)
    r.raise_for_status()
    data = r.json()
    
    if data["code"] != 0:
        raise RuntimeError(data)
    
    return data["data"]


def replies_extractor(data):
    """
    replies将获取的评论数据，仅保存最关键的信息
    """
    page = data["page"]
    replies = data["replies"]
    comments = []
    if not replies: return {"page": page, "comments": []}
    for reply in replies:
        comment = {
            "rpid": reply["rpid"],
            "uname": reply["member"]["uname"],
            "ctime": _timestamp_to_local_datetime(reply["ctime"]),
            "mid": reply["member"]["mid"],
            "message": reply["content"]["message"],
        }
        comments.append(comment)
        
    return {
        "page": page,
        "comments": comments,
    }


def _timestamp_to_local_datetime(timestamp, format_str="%Y-%m-%d %H:%M:%S"):
    """
    将 Unix 时间戳转换为本地日期和时间
    """
    utc_dt = datetime.datetime.fromtimestamp(timestamp, tz=datetime.timezone.utc)
    local_dt = utc_dt.astimezone()
    return local_dt.strftime(format_str)


def get_comments(aid: int, cookie: str | None = None, kwargs: dict | None = None):
    """
    获取视频的评论信息，格式如下：

    ```
    [
        {
            "rpid": "评论 ID",
            "uname": "用户名",
            "ctime": "评论时间",
            "mid": "用户ID",
            "message": "评论内容"
        },
        ...
    ]
    ```
    """
    data = get_video_replies(aid, cookie, kwargs)
    return replies_extractor(data).get("comments", [])
