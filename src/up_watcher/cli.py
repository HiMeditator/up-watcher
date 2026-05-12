import argparse
from .config import set_config
from .video import get_video_info
from .watcher import video_comments_watcher, video_comments_watcher_feishu


def main():
    parser = argparse.ArgumentParser(prog="up-watcher", description="Bilibili UP monitoring tool")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # set command
    parser_set = subparsers.add_parser("set", help="Set a config key-value pair")
    parser_set.add_argument("key", help="Config key name")
    parser_set.add_argument("value", help="Config value")
    # bvinfo command
    parser_bvinfo = subparsers.add_parser("bvinfo", help="Get video info by bvid")
    parser_bvinfo.add_argument("bvid", help="Video BV id, e.g. BV1xx411c7mD")
    # watch command
    parser_watch = subparsers.add_parser("watch", help="Watch UP's new comments of a video")
    parser_watch.add_argument("bvid", help="Video BV id, e.g. BV1xx411c7mD")
    parser_watch.add_argument("--interval", '-i', default=30, help="Query interval, default is 30 seconds, must greater than 5")
    parser_watch.add_argument("--watch-all", '-a', action='store_true', help="Watch comments from all users, not just the UP")
    parser_watch.add_argument("--feishu", '-f', action='store_true', help="Send new comments to Feishu")
    # stop command
    parser_stop = subparsers.add_parser("stop", help="Stop watching UP's new comments of a video")

    args = parser.parse_args()

    if args.command == "set":
        cli_set_config(args.key, args.value)
        
    elif args.command == "bvinfo":
        show_video_info(args.bvid)
    
    elif args.command == "watch":
        if args.feishu:
            video_comments_watcher_feishu(args.bvid, args.interval, args.watch_all)
        else:
            video_comments_watcher(args.bvid, args.interval, args.watch_all)

    elif args.command == "stop":
        stop_watching()

def cli_set_config(key: str, value):
    set_config(key, value)
    print(f"{key} set successfully")

def show_video_info(bvid: str):
    video_info = get_video_info(bvid)
    print(f"Title: {video_info['title']}")
    print(f"UP Name: {video_info['up_name']}")
    print(f"UP MID: {video_info['up_mid']}")
    print(f"AID: {video_info['aid']}")

def stop_watching():
    set_config("stop", True)
