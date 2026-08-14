# Chathook Project Guide for AI Agents

## Project Overview

**Chathook** is a chat-to-Webhook relay station. It receives messages from various sources and forwards them to target platforms via Webhooks. The project uses a dual-tech-stack architecture with separated frontend and backend.

- **Repository**: [Chathook](https://github.com/mantoujun-lab/Chathook)
- **License**: Apache 2.0

## Tech Stack

### Backend (root directory)
- **Language**: Python 3.14+
- **Package Manager**: uv
- **Framework**: FastAPI + Uvicorn
- **HTTP Client**: httpx (async)
- **Validation**: Pydantic v2
- **Logging**: loguru
- **Storage**: JSON file (no database)

### Frontend (`dashboard/` directory)
- **Framework**: Nuxt 4 (Vue 3 + TypeScript)
- **Package Manager**: npm
- **Runtime**: Node.js 24 LTS
- **UI**: Nuxt UI v3 (Tailwind CSS v4 + Reka UI)
- **HTTP**: Nuxt built-in `useFetch` / `$fetch` (no axios)

## Directory Structure

```
Chathook/
├── main.py                     # FastAPI app entry point + 一键启动
├── src/                        # Backend Python package
│   ├── __init__.py
│   ├── chat/                   # Channel-agnostic abstractions
│   │   ├── __init__.py
│   │   ├── schemas.py          # Unified message models (MessagePayload, SendRequest, SendResult)
│   │   └── adapter.py          # OutboundAdapter ABC (base class for all channel adapters)
│   └── webhook/                # Webhook channel implementation
│       ├── __init__.py
│       ├── config.py           # ConfigManager (JSON config read/write)
│       ├── schema.py           # WebhookConfig, PlatformType, WebhookConfigFile
│       ├── adapters/           # Platform-specific adapters
│       │   ├── __init__.py     # Adapter registry (get_adapter)
│       │   ├── feishu.py       # Feishu/Lark webhook adapter
│       │   ├── dingtalk.py     # DingTalk webhook adapter
│       │   └── custom.py       # Custom webhook adapter
│       └── services/           # Business logic
│           ├── __init__.py
│           ├── sender.py       # SenderService (send + broadcast)
│           └── webhook_manager.py  # WebhookManager (CRUD)
├── dashboard/                  # Frontend Nuxt 4 app
│   ├── app/
│   │   ├── app.vue
│   │   ├── app.config.ts
│   │   ├── pages/
│   │   │   ├── index.vue      # Send message panel
│   │   │   └── webhooks.vue   # Webhook config management
│   │   ├── assets/
│   │   │   └── css/main.css       # Tailwind v4 + Nuxt UI entry
│   │   └── layouts/
│   │       └── default.vue
│   ├── nuxt.config.ts
│   ├── tsconfig.json
│   └── package.json
├── tests/
├── data/                      # Runtime data (webhooks.json auto-created)
├── AGENTS.md                  # This file
├── README.md
├── LICENSE
├── .gitattributes
├── .pre-commit-config.yaml
├── pyproject.toml
├── uv.lock
└── .gitignore
```

## Architecture: Adapter Pattern

The project follows an adapter pattern with two abstraction layers:

1. **`chat/`** — Channel-agnostic layer. Contains the unified message schema (`MessagePayload`) and the abstract base class (`OutboundAdapter`). This layer has zero knowledge of Webhook-specific concepts.

2. **`webhook/`** — Webhook channel implementation. Each platform (Feishu, DingTalk, Custom) has its own adapter that extends `OutboundAdapter`. The adapter registry (`get_adapter()`) maps `PlatformType` to the correct adapter class.

```
Dashboard (Nuxt 4)
    │
    │  POST /api/send
    ▼
FastAPI Backend
    │
    ├─ SenderService
    │   └─ get_adapter(config)  →  FeishuAdapter / DingTalkAdapter / CustomAdapter
    │                                  │
    │                                  ├─ build_payload()  (unified msg → platform payload)
    │                                  └─ send()           (httpx POST to webhook URL)
    │
    └─ WebhookManager → ConfigManager → data/webhooks.json
```

## Supported Platforms

Outbound 列表示出站方向（从 Chathook 发送到该平台）是否已经具备代码占位结构（适配器文件 + 平台枚举），Status 表示功能完备度：

| Platform | Inbound | Outbound | Status |
|---|---|---|---|
| Feishu/Lark | — | Adapter stub | Planned (payload skeleton, signature pending) |
| DingTalk | — | Adapter stub | Planned (payload skeleton, signature pending) |
| Custom Webhook | — | Adapter stub | Planned (payload skeleton, headers/content-type pending) |

## Key Design Decisions

- **No database**: All Webhook configurations are stored in `data/webhooks.json`. The `ConfigManager` class handles read/write with plain dict storage (no Pydantic models for config).
- **No authentication**: Currently no auth on the API. Will be added later.
- **CORS**: Wide-open in development (`allow_origins=["*"]`). Restrict in production.
- **Extensibility**: New channel types (e.g., direct API, WebSocket) can be added as new top-level directories under `src/` (e.g., `api/`, `websocket/`), reusing `chat/` abstractions.
- **Frontend proxy**: In dev, Nuxt proxies `/api` and `/health` to `http://127.0.0.1:8000`. In production, set `API_BASE` env var.

## Development Commands

### Backend

```bash
# Install dependencies
uv sync

# Run dev server (with hot reload)
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Or start backend + frontend together (one-key dev)
uv run python main.py

# Run tests
uv run pytest
```

### Frontend

```bash
cd dashboard
npm install
npm run dev          # Dev server on http://localhost:3000
npm run build        # Production build
npm run preview      # Preview production build
```

### Both (development)

Run two terminals:
1. Terminal 1: `uv run uvicorn main:app --reload --port 8000`
2. Terminal 2: `cd dashboard && npm run dev`

The Nuxt dev server proxies API calls to the FastAPI backend automatically.

## API Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Health check |
| GET | `/api/webhooks` | List all webhooks |
| GET | `/api/webhooks/{id}` | Get a webhook by ID |
| POST | `/api/webhooks` | Create a webhook |
| PUT | `/api/webhooks/{id}` | Update a webhook |
| DELETE | `/api/webhooks/{id}` | Delete a webhook |
| POST | `/api/send` | Send a message to a specific webhook |
| POST | `/api/broadcast` | Broadcast a message to multiple webhooks |

## Conventions

- **Python**: Use `from __future__ import annotations` in all modules. Type hints required. Follow PEP 8.
- **Imports**: Use relative imports within the package (e.g., `from ...chat.adapter import OutboundAdapter`).
- **Naming**: Files use `snake_case.py`. Classes use `PascalCase`. Constants use `UPPER_SNAKE_CASE`.
- **Vue/Nuxt**: Use `<script setup lang="ts">`. Composition API only. No Options API.
- **Commits**: Use conventional commits (`feat:`, `fix:`, `chore:`, `docs:`, `refactor:`).
- **Branches**: Feature branches named `feat/xxx`, `fix/xxx`, `refactor/xxx`.
