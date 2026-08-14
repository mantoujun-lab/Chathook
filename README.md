<div align="center">

<!-- Cover -->
![Chathook](https://socialify.git.ci/mantoujun-lab/Chathook/image?description=1&language=1&name=1&pattern=Overlapping+Hexagons&theme=Auto)

<!-- Status -->
[![GitHub License](https://img.shields.io/github/license/mantoujun-lab/Chathook?style=for-the-badge)](LICENSE)

<!-- Python Runtime -->
[![Python](https://img.shields.io/badge/Python-yellow?style=for-the-badge&logo=python&logoColor=white&label=3.14%2B&labelColor=blue)](https://www.python.org)
[![UV](https://img.shields.io/badge/UV-purple?style=for-the-badge&logo=uv&logoColor=white)](https://docs.astral.sh/uv/)

<!-- Web UI Runtime -->
[![NodeJS](https://img.shields.io/badge/NodeJS-green?style=for-the-badge&logo=node.js&logoColor=white&label=24)](https://nodejs.org)
![Nuxt](https://img.shields.io/badge/Nuxt-black?style=for-the-badge&logo=nuxt)

</div>

## 项目简介

Chathook 是一个 **聊天消息 Webhook 中转站**，用于接收统一格式的消息，然后通过适配器模式转换并转发到多个目标平台（飞书 / 钉钉 / 自定义 Webhook）。

- **统一入口**：一套 API 发送到所有平台
- **适配器模式**：新增平台只需添加对应 Adapter
- **Web 管理面板**：可视化管理 Webhook 配置与发送消息
- **零数据库依赖**：配置存储于本地 JSON 文件

## 技术栈

### 后端（根目录）
- **语言**：Python 3.14+
- **Web 框架**：FastAPI + Uvicorn
- **HTTP 客户端**：httpx（异步）
- **日志**：loguru
- **包管理**：uv
- **存储**：JSON 文件

### 前端（`dashboard/`）
- **框架**：Nuxt 4（Vue 3 + TypeScript）
- **UI 组件**：Nuxt UI v3（Tailwind CSS v4 + Reka UI）
- **运行时**：Node.js 24 LTS
- **包管理**：npm

## 本地运行

### 前置要求
- Python >= 3.14
- Node.js >= 24 LTS
- uv（Python 包管理器）
- npm

### 一键启动（推荐）

```bash
# 1. 安装后端依赖
uv sync

# 2. 安装前端依赖
cd dashboard
npm install
cd ..

# 3. 一键启动后端 + 前端
uv run python main.py
```

启动后访问：
- 前端面板：http://localhost:3000
- 后端 API：http://localhost:8000
- 健康检查：http://localhost:8000/health

### 分别启动

```bash
# 终端 1 - 后端（热重载）
uv sync
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 终端 2 - 前端
cd dashboard
npm install
npm run dev
```

## 许可证

本项目基于 [Apache License 2.0](LICENSE) 开源，详见 LICENSE 文件。
