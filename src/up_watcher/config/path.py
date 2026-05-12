from platformdirs import user_config_dir
from pathlib import Path


APP_NAME = "up-watcher"
config_dir = Path(user_config_dir(APP_NAME))
config_file = config_dir / "config.json"

print(f"Config file path: {config_file}")
