import json
from .path import config_file


def get_config() -> dict:
    if not config_file.exists():
        return {}
    with open(config_file, "r", encoding="utf-8") as f:
        return json.load(f)


def get_cookie() -> str | None:
    return get_config().get("cookie")
