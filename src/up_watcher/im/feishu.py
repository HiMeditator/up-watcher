import json
from ..config import get_config_value

import lark_oapi as lark
from lark_oapi.api.im.v1 import * # type: ignore


watch_info_str = ""
user_open_id = ""
client = None


def _handle_message(data: lark.im.v1.P2ImMessageReceiveV1):
    """处理用户发送的消息"""
    global user_open_id
    try:
        chat_id = data.event.message.chat_id # type: ignore
        sender = data.event.sender # type: ignore
        user_open_id = sender.sender_id.open_id # type: ignore
        
        print(f"收到来自用户 {user_open_id} 的消息")
        print(f"消息ID: {data.event.message.message_id}") # type: ignore
        print(f"聊天类型: {data.event.message.chat_type}") # type: ignore
        
        if data.event.message.message_type == "text": # type: ignore
            content = json.loads(data.event.message.content) # type: ignore
            user_text = content.get("text", "")
            print(f"消息内容: {user_text}")
            reply_text = f"✅ 收到你的消息：「{user_text}」\n\n监控信息：{watch_info_str}"
            _send_reply(chat_id, reply_text) # type: ignore
            
    except Exception as e:
        print(f"❌ 处理消息时发生错误: {e}")
        import traceback
        traceback.print_exc()


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
        print(f"✅ 回复成功，消息ID: {response.data.message_id}") # type: ignore
    else:
        print(f"❌ 回复失败: {response.code} - {response.msg}")
        print(f"错误详情: {response.raw.content}") # type: ignore

    return response


def _send_message_to_feishu_user(text: str) -> CreateMessageResponse:
    """给指定用户发送文本消息"""
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
        print(f"✅ 给用户 {user_open_id} 发送消息成功，消息ID: {response.data.message_id}") # type: ignore
    else:
        print(f"❌ 给用户 {user_open_id} 发送消息失败: {response.code} - {response.msg}")
        print(f"错误详情: {response.raw.content}") # type: ignore
    return response


def feishu_handle_new_comments(comments: list[dict]):
    comment_info = []
    for comment in comments:
        comment_info.append(f"{comment['uname']}[{comment['ctime']}]：{comment['message']}")
    _send_message_to_feishu_user("\n".join(comment_info))


def connect_feishu(watch_info: str):
    global watch_info_str
    global client
    watch_info_str = watch_info
    APP_ID = get_config_value("feishu_app_id")
    APP_SECRET = get_config_value("feishu_app_secret")

    if not APP_ID or not APP_SECRET:
        print("❌ 请先配置飞书 App ID 和 App Secret")
        print("upw set feishu_app_id <app_id>")
        print("upw set feishu_app_secret <app_secret>")
        return
    
    client = lark.Client.builder() \
        .app_id(APP_ID) \
        .app_secret(APP_SECRET) \
        .log_level(lark.LogLevel.INFO) \
        .build()

    event_handler = lark.EventDispatcherHandler.builder("", "") \
        .register_p2_im_message_receive_v1(_handle_message) \
        .build()

    ws_client = lark.ws.Client(
        APP_ID,
        APP_SECRET,
        event_handler=event_handler,
        log_level=lark.LogLevel.INFO
    )
    
    print("🤖 飞书机器人已启动！")
    print("现在打开飞书，给飞书机器人发送任意消息，即可开始监控")
    ws_client.start()
