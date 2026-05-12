import json
import asyncio
import threading
from queue import Queue, Empty
from time import monotonic, sleep

from .. import console
from ..config import get_config_value

import lark_oapi as lark
from lark_oapi.api.im.v1 import * # type: ignore


watch_info_str = ""
user_open_id = None
client = None
ws_client = None
ws_thread = None
missing_user_warning_shown = False


def _handle_message(data: lark.im.v1.P2ImMessageReceiveV1):
    """处理用户发送的消息"""
    global user_open_id
    try:
        chat_id = data.event.message.chat_id # type: ignore
        sender = data.event.sender # type: ignore
        user_open_id = sender.sender_id.open_id # type: ignore

        console.info(f"收到飞书消息：用户 {user_open_id}") # type: ignore
        console.info(f"消息 ID：{data.event.message.message_id}") # type: ignore
        console.info(f"聊天类型：{data.event.message.chat_type}") # type: ignore
        
        if data.event.message.message_type == "text": # type: ignore
            content = json.loads(data.event.message.content) # type: ignore
            user_text = content.get("text", "")
            console.info(f"消息内容：{user_text}")
            reply_text = f"✅ 收到你的消息：「{user_text}」\n\n监控信息：\n{watch_info_str}"
            _send_reply(chat_id, reply_text) # type: ignore
            
    except Exception as e:
        console.error(f"处理飞书消息时发生错误：{e}")


def _send_reply(chat_id: str, text: str):
    """发送回复消息"""
    request = CreateMessageRequest.builder() \
        .receive_id_type("chat_id") \
        .request_body(CreateMessageRequestBody.builder()
            .receive_id(chat_id)
            .msg_type("text")
            .content(json.dumps({"text": text}))
            .build()) \
        .build()
    
    response = client.im.v1.message.create(request) # type: ignore

    if response.success():
        console.success(f"飞书回复已发送，消息 ID：{response.data.message_id}") # type: ignore
    else:
        console.error(f"飞书回复失败：{response.code} - {response.msg}")
        console.error(f"错误详情：{response.raw.content}") # type: ignore

    return response


def _send_message_to_feishu_user(text: str) -> CreateMessageResponse | None:
    """给指定用户发送文本消息"""
    global missing_user_warning_shown
    if not user_open_id:
        if not missing_user_warning_shown:
            console.warning("尚未收到飞书用户消息，暂时无法推送；请先在飞书中给机器人发送任意消息")
            missing_user_warning_shown = True
        return None

    request = CreateMessageRequest.builder() \
        .receive_id_type("open_id") \
        .request_body(CreateMessageRequestBody.builder()
            .receive_id(user_open_id) # type: ignore
            .msg_type("text")
            .content(json.dumps({"text": text}))
            .build()) \
        .build()
    
    response = client.im.v1.message.create(request) # type: ignore

    if response.success():
        console.success(f"已向用户 {user_open_id} 推送飞书消息，消息 ID：{response.data.message_id}") # type: ignore
    else:
        console.error(f"向用户 {user_open_id} 推送飞书消息失败：{response.code} - {response.msg}")
        console.error(f"错误详情：{response.raw.content}") # type: ignore
    return response


def _run_ws_client(
    app_id: str,
    app_secret: str,
    event_handler,
    startup_errors: Queue,
) -> None:
    global ws_client
    try:
        import lark_oapi.ws.client as lark_ws_client

        ws_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(ws_loop)
        lark_ws_client.loop = ws_loop

        ws_client = lark.ws.Client(
            app_id,
            app_secret,
            event_handler=event_handler,
            log_level=lark.LogLevel.ERROR
        )
        ws_client.start()
    except Exception as exc:
        try:
            startup_errors.put_nowait(exc)
        except Exception:
            pass
        console.error(f"飞书长连接启动失败：{exc}")


def _wait_for_ws_start(startup_errors: Queue, timeout: float = 5.0) -> bool:
    deadline = monotonic() + timeout
    while monotonic() < deadline:
        try:
            exc = startup_errors.get_nowait()
        except Empty:
            exc = None

        if exc is not None:
            console.error(f"飞书机器人启动失败：{exc}")
            return False

        if ws_client is not None and getattr(ws_client, "_conn", None) is not None:
            console.success("飞书机器人已启动")
            return True

        if ws_thread is not None and not ws_thread.is_alive():
            console.error("飞书机器人启动失败：长连接线程已退出")
            return False

        sleep(0.1)

    console.warning("飞书长连接仍在后台建立中，评论监控将继续启动")
    return True


def is_feishu_connect_to_user() -> bool:
    global user_open_id
    return user_open_id is not None


def feishu_handle_new_comments(comments: list[dict]):
    comment_info = []
    for comment in comments:
        comment_info.append(f"{comment['uname']}（{comment['ctime']}）：{comment['message']}")
    _send_message_to_feishu_user("\n".join(comment_info))


def connect_feishu(watch_info: str) -> bool:
    global watch_info_str
    global client
    global ws_thread
    watch_info_str = watch_info
    APP_ID = get_config_value("feishu_app_id")
    APP_SECRET = get_config_value("feishu_app_secret")

    if not APP_ID or not APP_SECRET:
        console.error("请先配置飞书应用 ID 和应用密钥，命令如下：")
        console.command_hint("upw set feishu_app_id <app_id>")
        console.command_hint("upw set feishu_app_secret <app_secret>")
        return False
    
    client = lark.Client.builder() \
        .app_id(APP_ID) \
        .app_secret(APP_SECRET) \
        .log_level(lark.LogLevel.ERROR) \
        .build()

    event_handler = lark.EventDispatcherHandler.builder("", "") \
        .register_p2_im_message_receive_v1(_handle_message) \
        .build()
    
    console.info("在飞书中向机器人发送任意消息后，即可开始接收监控推送")
    startup_errors = Queue(maxsize=1)
    ws_thread = threading.Thread(
        target=_run_ws_client,
        args=(APP_ID, APP_SECRET, event_handler, startup_errors),
        name="up-watcher-feishu-ws",
        daemon=True,
    )
    ws_thread.start()

    return _wait_for_ws_start(startup_errors)
