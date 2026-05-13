# Up Watcher

Up Watcher 是一个用于监控 Bilibili 视频评论的命令行工具。它可以按固定间隔轮询指定视频的最新评论，默认只关注 UP 主本人的评论，也可以切换为监听全部评论；发现新评论时会在终端显示，并可选择播放提示音或推送到飞书机器人。

![Up Watcher 飞书推送示例](https://raw.githubusercontent.com/HiMeditator/up-watcher/main/docs/img/03.png)

## 功能特性

- **视频信息查询**：根据 BV 号查询标题、UP 主、UP 主编号和视频 AID；该功能不需要 Cookie。
- **评论轮询监控**：拉取视频最新评论，基于评论 ID 识别本次进程内尚未出现过的新评论。
- **监听范围可选**：默认只监听 UP 主评论，使用 `-a` / `--watch-all` 可监听所有用户评论。
- **自定义轮询间隔**：默认 30 秒；当间隔设置为 5 秒及以下时，会启用面向 A 股交易时段的智能间隔。
- **中文终端输出**：提供中文帮助、中文错误提示、时间戳、分区线和倒计时显示。
- **声音提醒**：使用 `-s` / `--sound` 后，发现新评论时播放内置 `ring.wav`。
- **飞书推送**：使用 `-f` / `--feishu` 后，可将新评论通过飞书机器人推送给已连接用户。
- **配置管理**：通过 `upw set` 写入本机用户配置目录，可保存 Bilibili Cookie、飞书应用配置和停止标记。

## 环境要求

- Python 3.10+
- 开发环境推荐使用 [uv](https://docs.astral.sh/uv/)

项目依赖在 [pyproject.toml](./pyproject.toml) 中声明：

- `requests`：访问 Bilibili API
- `platformdirs`：解析跨平台用户配置目录
- `lark-oapi`：可选依赖，用于连接飞书开放平台并收发消息
- `simpleaudio`：可选依赖，非 Windows 平台播放提示音；Windows 平台使用标准库 `winsound`

## 安装与使用

### 正式使用

推荐使用 uv 从 PyPI 安装为本机命令行工具：

```bash
uv tool install up-watcher
```

如果需要飞书推送或非 Windows 平台声音提醒，可安装对应可选依赖：

```bash
uv tool install "up-watcher[feishu]"
uv tool install "up-watcher[sound]"
uv tool install "up-watcher[all]"
```

也可以不安装，直接临时运行：

```bash
uvx --from up-watcher upw --help
uvx --from up-watcher upw bvinfo BV1xx411c7mD
```

使用 pip 安装基础功能：

```bash
pip install up-watcher
```

pip 同样支持可选依赖：

```bash
pip install "up-watcher[feishu]"
pip install "up-watcher[sound]"
pip install "up-watcher[all]"
```

### 🚀 开发场景

在项目目录内开发时同步依赖：

```bash
uv sync
uv sync --extra all --group dev
```

开发时可直接用 `uv run` 运行：

```bash
uv run upw --help
uv run upw bvinfo BV1xx411c7mD
```

也可以安装为本机命令行工具：

```bash
uv tool install .
```

如果希望以可编辑模式安装，便于修改源码后立即生效：

```bash
uv tool install -e .
```

安装完成后使用 `upw` 命令。帮助文本中的程序名由 argparse 设置为 `up-watcher`，但实际入口命令是 `upw`。

## 配置

配置写入 `platformdirs.user_config_dir("up-watcher")` 下的 `config.json`。常见位置如下：

- Windows：`%LOCALAPPDATA%\up-watcher\up-watcher\config.json`
- macOS：`~/Library/Application Support/up-watcher/config.json`
- Linux：`~/.config/up-watcher/config.json`

### 设置 Bilibili Cookie

`watch` 命令通常需要登录后的 Bilibili Cookie 才能稳定获取评论。`bvinfo` 不需要 Cookie。

获取 Cookie 的一种方式：

1. 登录 [Bilibili](https://www.bilibili.com)。
2. 打开浏览器开发者工具。
3. 在 Network / 网络面板中打开任意 Bilibili 请求。
4. 从请求头中复制完整的 `Cookie` 字段。

写入配置：

```bash
upw set cookie "your_bilibili_cookie_string"
```

Cookie 和飞书密钥会以明文保存在本机配置文件中，请不要提交或分享该文件。

### 设置飞书配置

如果是从 PyPI 安装，请确认已安装飞书可选依赖：

```bash
pip install "up-watcher[feishu]"
```

配置与使用飞书机器人推送最新评论消息请参考该文档：[feishu_robot.md](./docs/feishu_robot.md)。

使用飞书推送时，工具会启动飞书长连接并等待用户在飞书中给机器人发送任意消息。收到用户消息后，工具会记录该用户的 `open_id`，后续新评论会推送给该用户。

飞书应用侧需要具备接收消息事件和发送文本消息的权限；如果连接或推送失败，终端会输出飞书接口返回的错误信息。

### 有效配置项

| 配置项 | 说明 |
| --- | --- |
| `cookie` | 登录 Bilibili 后的 Cookie，用于获取评论 |
| `feishu_app_id` | 飞书应用 App ID，用于 `--feishu` 推送 |
| `feishu_app_secret` | 飞书应用 App Secret，用于 `--feishu` 推送 |
| `stop` | 停止监控标记，`upw stop` 会将它设置为 `True` |

`upw set` 可以写入任意键值，但当前代码实际读取的是上表中的配置。

## 命令说明

### `upw set`

写入一个配置项。

```bash
upw set <key> <value>
```

示例：

```bash
upw set cookie "buvid3=xxx; SESSDATA=xxx; ..."
upw set feishu_app_id "cli_xxx"
upw set feishu_app_secret "xxx"
```

### `upw bvinfo`

查询视频基础信息。

```bash
upw bvinfo <bvid>
```

示例：

```bash
upw bvinfo BV1GJ411x7h7
```

输出示例：

```text
23:40:12 信息 正在获取视频信息...

 视频信息 ─────────────────────────────────────────────
标题：【官方 MV】Never Gonna Give You Up - Rick Astley
UP 主：索尼音乐中国
UP 主编号：486906719
视频编号：80433022
──────────────────────────────────────────────────────
```

### `upw watch`

监控指定视频的评论，每次会拉取最新的 20 条评论，并检查其中是否有新评论。

```bash
upw watch <bvid> [-i <seconds>] [-a] [-s] [-f]
```

| 参数 | 默认值 | 说明 |
| --- | --- | --- |
| `bvid` | 无 | 视频 BV 号，例如 `BV1xx411c7mD` |
| `-i`, `--interval` | `30` | 轮询间隔，单位秒；必须大于 0 |
| `-a`, `--watch-all` | `False` | 监听全部评论；默认只监听 UP 主评论 |
| `-s`, `--sound` | `False` | 发现新评论时播放声音提醒 |
| `-f`, `--feishu` | `False` | 发现新评论时推送到飞书机器人 |

示例：

```bash
# 默认每 30 秒检查一次，仅监听 UP 主评论
upw watch BV1xx411c7mD

# 每 60 秒检查一次
upw watch BV1xx411c7mD -i 60

# 监听全部评论
upw watch BV1xx411c7mD -a

# 发现新评论时播放提示音
upw watch BV1xx411c7mD -s

# 推送到飞书，并同时播放提示音
upw watch BV1xx411c7mD -f -s

# 设置为 5 秒及以下，启用智能间隔
upw watch BV1xx411c7mD -i 1
```

首次拉取评论时，当前最新一批符合条件的评论会被加入内存中的已见列表，并作为本次运行发现的评论显示。之后的轮询只会显示本进程内未见过的评论 ID。

### 智能间隔

当 `--interval` 设置为 5 秒及以下时，工具不会真的每 1 到 5 秒访问一次接口，而是根据本地时间切换为以下等待时间：

| 本地时段 | 等待时间 |
| --- | --- |
| 09:20 ~ 09:40 | 20 ~ 30 秒 |
| 09:40 ~ 11:30 | 40 ~ 60 秒 |
| 13:00 ~ 15:00 | 90 ~ 120 秒 |
| 其他时间 | 300 秒 |

该逻辑主要面向 A 股相关视频的盘中评论监控。

### `upw stop`

请求停止正在运行的监控。

```bash
upw stop
```

使用方式：

- 在另一个终端执行 `upw stop`。
- 或在监控进程中按 `Ctrl+C`。

`upw stop` 的实现是将配置项 `stop` 写为 `True`。监控进程在倒计时期间每秒检查该配置，收到停止标记后会退出。

## 工作方式

`upw watch` 的核心流程如下：

1. 通过 Bilibili `x/web-interface/view` 接口把 BV 号解析为 AID，并获取 UP 主信息。
2. 通过 Bilibili `x/v2/reply` 接口获取最新的 20 条评论。
3. 从评论数据中提取 `rpid`、用户名、发布时间、用户 MID 和正文。
4. 根据 `watch_all` 决定只保留 UP 主评论或保留全部评论。
5. 使用内存中的 `comment_pool` 按 `rpid` 去重。
6. 发现新评论后输出到终端，并按参数触发声音提醒或飞书推送。

评论去重只在当前进程内有效，重启监控后会重新建立已见列表。

## 项目结构

```text
up-watcher/
├── pyproject.toml              # 项目元数据、依赖和 upw 入口
├── README.md
└── src/
    └── up_watcher/
        ├── cli.py              # argparse 命令行入口
        ├── console.py          # 中文终端输出和格式化
        ├── watcher.py          # 评论监控、智能间隔、声音/飞书触发
        ├── assets/
        │   └── ring.wav        # 声音提醒资源
        ├── config/
        │   ├── get_config.py   # 读取 config.json
        │   ├── set_config.py   # 写入/删除 config.json 配置
        │   └── path.py         # 用户配置路径
        ├── im/
        │   └── feishu.py       # 飞书长连接、收信和推送
        ├── utils/
        │   └── audio.py        # 跨平台播放 wav
        └── video/
            └── utils.py        # Bilibili 视频信息和评论 API
```

## 常见问题

### `bvinfo` 可以用，但 `watch` 抓不到评论？

通常是 Cookie 缺失、过期或权限不足。重新登录 Bilibili 后更新 Cookie：

```bash
upw set cookie "新的_cookie_值"
```

### 为什么设置 `-i 1` 后不是每秒请求一次？

`1` 到 `5` 秒会触发智能间隔模式，用于降低高频请求。需要固定间隔时，请设置大于 5 的秒数，例如：

```bash
upw watch BV1xx411c7mD -i 10
```

### 飞书推送没有收到消息？

请检查：

- 已配置 `feishu_app_id` 和 `feishu_app_secret`。
- 飞书应用已开通接收消息事件和发送消息所需权限。
- 运行 `upw watch ... -f` 后，已经在飞书中向机器人发送过任意消息。
- 终端中是否有飞书接口返回的错误码或错误详情。

### 声音提醒没有播放？

Windows 使用系统 `winsound` 播放。非 Windows 平台使用 `simpleaudio` 播放内置 wav 文件，请先安装 `up-watcher[sound]` 并确保系统有可用的音频输出环境。

## 注意事项

- 本工具依赖 Bilibili 和飞书开放平台接口，接口规则变化、登录状态变化或风控策略都可能影响结果。
- 请合理设置轮询间隔，避免过高频率请求。
- Cookie、飞书 App Secret 等敏感信息只应保存在本机，不要提交到仓库或贴到公开场合。
