# Up Watcher

Poll Bilibili UP data.

## 安装 CLI 工具

正式使用：将当前目录下的 Python 项目作为可执行工具安装到系统中

```bash
uv tool install .
```

开发使用：将当前目录的 Python 项目以可编辑模式安装为全局命令行工具

```bash
uv tool install . -e
```

## 使用

### 设置配置

```bash
upw set cookie "your_cookie_string"
```

### 获取视频信息

```bash
upw bvinfo BV1xx411c7mD
```

这将显示视频标题、UP主名称、UP主MID、AID。

### 监控 UP 主视频最新评论

```bash
upw watch BV1xx411c7mD
```

运行该命令后，将开始监控该视频的评论。当有新的评论时，将显示评论信息。
