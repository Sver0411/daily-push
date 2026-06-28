# 📅 daily-push

> Daily course schedule + weather notifier for Feishu/Lark · Zero dependencies · Docker-ready

[![Python](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/docker-ready-2496ED?logo=docker)](https://hub.docker.com/)
[![License](https://img.shields.io/badge/license-MIT-green)](./LICENSE)
[![Lines](https://img.shields.io/badge/code-~330_lines-lightgrey)](./daily_push.py)

每天 7:30 自动推送当日课表 + 天气到飞书群 — 纯 Python 标准库，无第三方依赖，Docker 一键部署。

---

## ✨ Features

| 功能 | 说明 |
|------|------|
| 📚 课表推送 | 自动匹配当前周次，推送当日课程 |
| 🌤 天气查询 | 通过 wttr.in 获取天气（免费，无需 API Key） |
| 🔁 周次解析 | 支持 `1-16`、`4-16 双`、`1,3-8` 等灵活格式 |
| 🐳 Docker 化 | Alpine 镜像仅 ~80MB，`docker run` 即用 |
| 📡 飞书集成 | 通过自定义机器人 Webhook 推送到群聊 |
| 🔧 模拟模式 | `python daily_push.py sim 2 5` 模拟周三第5周 |

---

## 🚀 Quick Start

### 1. Clone

```bash
git clone https://github.com/<your-username>/daily-push.git
cd daily-push
```

### 2. Configure

编辑 `daily_push.py` 中的 `COURSES` 列表，填入你自己的课程：

```python
COURSES = [
    # day: 0=周一, 1=周二, ... 4=周五
    # period: (start, end) 节次
    {"day": 0, "name": "高等数学", "teacher": "张老师",
     "weeks_desc": "1-16", "period": (1, 2), "classroom": "教学楼A101"},
    # ... 更多课程
]
```

同时修改 `SEMESTER_START` 为你的学期第一周周一日期：

```python
SEMESTER_START = date(2026, 3, 9)  # 改成你的开学日期
```

### 3. Run

```bash
# 纯 Python（仅打印，不发送）
CITY="上海" python3 daily_push.py

# 模拟某一天（周三，第5周）
python3 daily_push.py sim 2 5

# 打印完整课表
python3 daily_push.py full
```

### 4. Docker

```bash
# 构建镜像
docker build -t daily-push .

# 运行（仅打印）
docker run --rm daily-push

# 发送到飞书
docker run --rm \
  -e FEISHU_WEBHOOK="https://open.feishu.cn/open-apis/bot/v2/hook/xxx" \
  -e CITY="北京" \
  daily-push
```

### 5. Cron (定时任务)

```bash
# 每天 7:30 推送
crontab -e
# 添加：
30 7 * * * docker run --rm -e FEISHU_WEBHOOK="https://open.feishu.cn/..." daily-push
```

---

## 📋 Week Format

`weeks_desc` 字段支持以下格式：

| 写法 | 含义 |
|------|------|
| `1-16` | 第 1~16 周 |
| `4-16e` | 第 4~16 周的**双周**（even weeks） |
| `1,3-8,10` | 第 1 周 + 3~8 周 + 10 周 |
| `5` | 仅第 5 周 |

> 注：原中文「双」改为 `e` (even)，保持纯 ASCII。

---

## 🏗️ Project Structure

```
daily-push/
├── daily_push.py    # 主脚本（330行，纯 stdlib）
├── Dockerfile        # Docker 构建文件
├── run.sh            # 快捷运行脚本
├── .gitignore
├── LICENSE           # MIT
└── README.md
```

---

## 🌤️ Weather Provider

使用 [wttr.in](https://wttr.in) — 免费、无需注册、全球城市支持。

```
https://wttr.in/Beijing?format=j1
```

天气描述自动英译中（sunny→晴, light rain→小雨 等）。

---

## 🛠️ Tech Stack

- **Runtime:** Python 3.8+ (stdlib only — `json`, `urllib`, `datetime`, `re`)
- **Container:** Docker (python:3.11-alpine, ~80MB)
- **Weather:** wttr.in
- **Notification:** Feishu/Lark Custom Bot Webhook

---

## 📝 License

MIT © 2026

---

## 🙋 FAQ

**Q: 周末会推送吗？**
A: 会的，显示「🎉 周末愉快，今天没有课程～」+ 天气。

**Q: 怎么获取飞书 Webhook URL？**
A: 飞书群 → 设置 → 群机器人 → 添加自定义机器人 → 复制 Webhook 地址。

**Q: 可以推送到钉钉/企业微信吗？**
A: 可以，修改 `send_feishu()` 函数中的消息格式即可，结构很相似。
