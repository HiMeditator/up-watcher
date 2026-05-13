import argparse
import sys

from . import console
from .config import set_config
from .video import get_video_info
from .watcher import video_comments_watcher, video_comments_watcher_feishu


class ChineseArgumentParser(argparse.ArgumentParser):
    def format_usage(self) -> str:
        return _translate_help(super().format_usage())

    def format_help(self) -> str:
        return _translate_help(super().format_help())

    def error(self, message: str):
        self.print_usage(sys.stderr)
        self.exit(2, f"{self.prog}: 错误：{_translate_error(message)}\n")


def _translate_help(text: str) -> str:
    return (
        text.replace("usage:", "用法:")
        .replace("positional arguments:", "位置参数:")
        .replace("optional arguments:", "选项:")
        .replace("options:", "选项:")
    )


def _translate_error(message: str) -> str:
    replacements = {
        "the following arguments are required:": "缺少必填参数：",
        "unrecognized arguments:": "无法识别的参数：",
        "invalid choice:": "无效选择：",
        "(choose from": "（可选：",
        "argument ": "参数 ",
    }
    for source, target in replacements.items():
        message = message.replace(source, target)
    return message.replace(")", "）")


def _interval_seconds(value: str) -> int:
    try:
        interval = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("请输入有效的秒数") from exc
    if interval <= 0:
        raise argparse.ArgumentTypeError("轮询间隔必须大于 0 秒")
    return interval


def main():
    parser = ChineseArgumentParser(
        prog="up-watcher",
        description="Bilibili UP 主评论监控工具",
        add_help=False,
    )
    parser.add_argument("-h", "--help", action="help", help="显示帮助信息并退出")
    subparsers = parser.add_subparsers(dest="command", required=True, title="可用命令", metavar="命令")

    parser_set = subparsers.add_parser("set", help="设置配置项", add_help=False)
    parser_set.add_argument("-h", "--help", action="help", help="显示帮助信息并退出")
    parser_set.add_argument("key", metavar="配置项", help="配置项名称")
    parser_set.add_argument("value", metavar="值", help="配置项的值")

    parser_bvinfo = subparsers.add_parser("bvinfo", help="查询视频信息", add_help=False)
    parser_bvinfo.add_argument("-h", "--help", action="help", help="显示帮助信息并退出")
    parser_bvinfo.add_argument("bvid", metavar="BV号", help="视频 BV 号，例如 BV1xx411c7mD")

    parser_watch = subparsers.add_parser("watch", help="监控视频的新评论", add_help=False)
    parser_watch.add_argument("-h", "--help", action="help", help="显示帮助信息并退出")
    parser_watch.add_argument("bvid", metavar="BV号", help="视频 BV 号，例如 BV1xx411c7mD")
    parser_watch.add_argument(
        "--interval", "-i",
        default=30,
        type=_interval_seconds,
        metavar="秒数",
        help="轮询间隔，默认 30 秒；设置为 5 秒及以下时启用智能间隔",
    )
    parser_watch.add_argument(
        "--watch-all", "-a",
        action="store_true",
        help="监控所有用户评论，默认仅监控 UP 主评论",
    )
    parser_watch.add_argument(
        "--sound", "-s",
        action="store_true",
        help="发现新评论消息时播放声音提醒"
    )
    parser_watch.add_argument(
        "--feishu", "-f",
        action="store_true",
        help="将新评论消息推送到飞书机器人"
    )


    parser_stop = subparsers.add_parser("stop", help="停止正在运行的监控", add_help=False)
    parser_stop.add_argument("-h", "--help", action="help", help="显示帮助信息并退出")

    args = parser.parse_args()

    console.info("详细教程请参考：https://github.com/HiMeditator/up-watcher")

    try:
        if args.command == "set":
            cli_set_config(args.key, args.value)

        elif args.command == "bvinfo":
            show_video_info(args.bvid)

        elif args.command == "watch":
            if args.feishu:
                video_comments_watcher_feishu(args.bvid, args.interval, args.watch_all, args.sound)
            else:
                video_comments_watcher(args.bvid, args.interval, args.watch_all, args.sound)

        elif args.command == "stop":
            stop_watching()
    except KeyboardInterrupt:
        console.warning("已中断，监控已退出")
    except Exception as exc:
        console.error(f"执行失败：{exc}")
        raise SystemExit(1) from exc


def cli_set_config(key: str, value):
    set_config(key, value)
    console.success(f"配置项「{key}」已保存")


def show_video_info(bvid: str):
    console.info("正在获取视频信息...")
    video_info = get_video_info(bvid)
    console.show_video_info(video_info)


def stop_watching():
    set_config("stop", True)
    console.success("已发送停止监控指令")
