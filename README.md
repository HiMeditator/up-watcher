# Up Watcher

一个用于轮询监控哔哩哔哩 UP 主视频最新评论的工具。当检测到 UP 主发布新评论时，会实时显示评论内容。

## 功能特性

- **中文输出**：工具输出信息为中文，适合中文用户
- **评论监控**：监控指定视频的评论，实时检测 UP 主的新评论
- **智能间隔**：支持自定义轮询间隔，当间隔小于等于 5 秒时自动启用特殊时间间隔
- **配置管理**：通过命令行轻松管理配置
- **视频信息查询**：无需 Cookie 即可查询视频基本信息

## 安装

安装前需要先确保本机有 Python 3.12+ 环境，并安装了 `uv`。

### 正式安装

将项目安装为全局命令行工具：

```bash
uv tool install .
```

### 开发模式安装

以可编辑模式安装，方便开发调试：

```bash
uv tool install . -e
```

安装完成后，使用 `upw` 命令调用工具。

## 配置

### 设置 Cookie

Cookie 是获取评论的必要配置，仅需设置一次。当 Cookie 过期时才需要重新设置。

**获取 Cookie 的方法**：
1. 登录 [Bilibili](https://www.bilibili.com)
2. 按 F12 打开开发者工具
3. 在 Network（网络）标签中，任意找一个 b站的请求
4. 在请求头中找到 `Cookie` 字段，复制其完整值

**设置 Cookie**：
```bash
upw set cookie "your_bilibili_cookie_string"
```

### 生效配置项

| 配置项 | 说明 |
|--------|------|
| `cookie` | 登录 Bilibili 后的 Cookie，用于获取评论 |
| `stop` | 停止监控标志，设为 `True` 可停止正在运行的监控 |

## 命令详解

### `upw set` - 设置配置

设置一个配置键值对。

```bash
upw set <key> <value>
```

**示例**：
```bash
# 设置 Cookie
upw set cookie "buvid3=xxx;CURRENT_FNVAL=xxx;..."

# 设置其他配置
upw set custom_key custom_value
```

### `upw bvinfo` - 获取视频信息

根据视频 BV 号获取视频基本信息，无需 Cookie 即可使用。

```bash
upw bvinfo <bvid>
```

**示例**：
```bash
upw bvinfo BV1GJ411x7h7
```

**输出示例**：
```
23:40:12 信息 正在获取视频信息...

 视频信息 ─────────────────────────────────────────────
标题：【官方 MV】Never Gonna Give You Up - Rick Astley
UP 主：索尼音乐中国
UP 主编号：486906719
视频编号：80433022
──────────────────────────────────────────────────────
```

### `upw watch` - 监控评论

监控指定视频的最新评论，实时检测新评论并显示。默认仅监控 UP 主本人的评论，使用 `-a` 参数可监控所有用户评论。

```bash
upw watch <bvid> [-i <interval>] [-a]
```

**参数说明**：
| 参数 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `bvid` | 是 | - | 视频 BV 号，如 `BV1xx411c7mD` |
| `-i`, `--interval` | 否 | 30 | 轮询间隔（秒），必须大于 5 |
| `-a`, `--watch-all` | 否 | False | 监控所有用户评论，默认为仅监控 UP 主评论 |

**特殊轮询逻辑**：
- 当设置的间隔大于 5 秒时：按指定间隔轮询
- 当设置的间隔小于等于 5 秒时：自动启用 A 股交易时段智能间隔

**A 股交易时段智能间隔**：
| 时段 | 间隔范围 |
|------|----------|
| 09:20 ~ 09:40 | 20~30 秒 |
| 09:40 ~ 11:30 | 40~60 秒 |
| 13:00 ~ 15:00 | 90~120 秒 |
| 其他时间 | 300 秒 |

**示例**：
```bash
# 每 60 秒轮询一次
upw watch BV1xx411c7mD -i 60

# 使用默认 30 秒间隔
upw watch BV1xx411c7mD

# 启用智能间隔（设置间隔 <= 5 即可）
upw watch BV1xx411c7mD -i 1

# 监控所有用户评论
upw watch BV1xx411c7mD -a
```

**输出示例**：
```
23:40:12 信息 正在获取视频信息...

 视频信息 ─────────────────────────────────────────────
标题：xxx
UP 主：xxx
UP 主编号：12345678
视频编号：12345678
──────────────────────────────────────────────────────

 监控设置 ─────────────────────────────────────────────
监听范围：仅 UP 主评论
轮询间隔：30 秒
飞书推送：未开启
──────────────────────────────────────────────────────

23:40:13 信息 正在获取评论...

 发现 1 条新评论 ───────────────────────────────────────
1. 用户名
   时间：2026-05-12 23:40:00
   内容：这是一条新评论
──────────────────────────────────────────────────────
```

### `upw stop` - 停止监控

停止正在运行的评论监控。

```bash
upw stop
```

**使用方式**：
- 新开一个终端窗口执行 `upw stop`
- 或直接结束监控进程（Ctrl+C）

## 使用场景示例

### 场景一：监控 A 股相关视频

有些 UP 主会在交易时段发布盘中分析，非常适合使用智能间隔：

```bash
# 设置小间隔触发智能间隔模式
upw watch BV1xx411c7mD -i 1
```

### 场景二：快速轮询高互动视频

当视频热度高、评论更新快时，可以使用较短间隔：

```bash
upw watch BV1xx411c7mD -i 10 -a
```

### 场景三：低频监控日常视频

对于更新频率低的视频，使用较长间隔节省资源：

```bash
upw watch BV1xx411c7mD -i 300  # 5 分钟
```

## 常见问题

### Q: 为什么评论抓取不到？

A: 可能是 Cookie 过期或无效。请重新登录 Bilibili 并更新 Cookie：
```bash
upw set cookie "新的_cookie_值"
```

### Q: 无 Cookie 能使用吗？

A: `bvinfo` 命令可以在无 Cookie 状态下使用，但 `watch` 命令需要 Cookie 才能获取评论。

### Q: 配置文件在哪里？

A: 配置文件位于用户配置目录：
- **Windows**: `C:\Users\<用户名>\AppData\Local\up-watcher\up-watcher\config.json`
- **Linux/macOS**: `~/.config/up-watcher/config.json`

### Q: 如何查看当前配置？

A: 直接读取配置文件：
```bash
# Windows
type %LOCALAPPDATA%\up-watcher\up-watcher\config.json

# Linux/macOS
cat ~/.config/up-watcher/config.json
```

## 项目结构

```
up-watcher/
├── src/up_watcher/
│   ├── __init__.py
│   ├── cli.py          # 命令行入口
│   ├── watcher.py     # 评论监控核心逻辑
│   ├── config/         # 配置管理
│   │   ├── get_config.py
│   │   ├── set_config.py
│   │   └── path.py
│   └── video/          # 视频信息及评论
│       └── utils.py
└── pyproject.toml
```

## 技术栈

- Python 3.12+
- [requests](https://requests.readthedocs.io/) - HTTP 客户端
- [platformdirs](https://pypi.org/project/platformdirs/) - 跨平台配置路径
