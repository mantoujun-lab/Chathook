"""Webhook 配置 CRUD 回归测试.

覆盖范围:
  - WebhookManager 直连 (业务层, 不经过 HTTP)
  - FastAPI 路由层 (验证 extra: None 规范化为 {} 后响应 200/201)
  - 未知字段、重复 ID、未知 ID 等边界

数据隔离: 用 pytest tmp_path 让 ConfigManager 写入临时目录, 避免污染
仓库根的 data/webhooks.json.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from main import app
from src.webhook.config import ConfigManager
from src.webhook.services.webhook_manager import WebhookManager


@pytest.fixture
def manager(tmp_path) -> WebhookManager:
    """指向临时目录的 WebhookManager, 测试间互不污染."""
    return WebhookManager(ConfigManager(data_dir=tmp_path))


@pytest.fixture
def client(manager: WebhookManager, monkeypatch) -> TestClient:
    """替换 api._manager 指向临时 manager, 避免 HTTP 测试落盘到 data/."""
    from src.webhook import api as api_mod

    monkeypatch.setattr(api_mod, "_manager", manager)
    return TestClient(app)


def _sample(**overrides) -> dict:
    """生成一条合规的 webhook 配置, 支持字段覆盖."""
    base = {
        "id": "wh-1",
        "name": "测试 webhook",
        "platform": "feishu",
        "url": "https://example.com/hook",
        "secret": None,
        "extra": {"k": "v"},
        "enabled": True,
    }
    base.update(overrides)
    return base


# -------------------- WebhookManager 直连 --------------------


def test_list_empty(manager: WebhookManager) -> None:
    assert manager.list() == []


def test_create_and_get(manager: WebhookManager) -> None:
    manager.create(_sample())
    got = manager.get("wh-1")
    assert got is not None
    assert got["id"] == "wh-1"
    assert got["name"] == "测试 webhook"


def test_create_duplicate_id_raises(manager: WebhookManager) -> None:
    manager.create(_sample())
    with pytest.raises(ValueError, match="ID 已存在"):
        manager.create(_sample())


def test_update_partial(manager: WebhookManager) -> None:
    manager.create(_sample())
    updated = manager.update("wh-1", {"name": "新名", "enabled": False})
    assert updated is not None
    assert updated["name"] == "新名"
    assert updated["enabled"] is False
    # 未触及的字段保持原值
    assert updated["url"] == "https://example.com/hook"
    assert updated["extra"] == {"k": "v"}


def test_update_rejects_unknown_key(manager: WebhookManager) -> None:
    manager.create(_sample())
    with pytest.raises(KeyError, match="不允许修改字段"):
        manager.update("wh-1", {"evil": "x"})


def test_update_unknown_id_returns_none(manager: WebhookManager) -> None:
    manager.create(_sample())
    assert manager.update("missing", {"name": "x"}) is None


def test_delete(manager: WebhookManager) -> None:
    manager.create(_sample())
    assert manager.delete("wh-1") is True
    assert manager.get("wh-1") is None
    assert manager.delete("wh-1") is False


# -------------------- FastAPI 路由层 (回归 extra: None 500 bug) --------------------


def test_api_create_then_list(client: TestClient) -> None:
    r = client.post("/api/webhooks", json=_sample())
    assert r.status_code == 201
    body = r.json()
    assert body["id"] == "wh-1"
    assert body["extra"] == {"k": "v"}

    r = client.get("/api/webhooks")
    assert r.status_code == 200
    assert len(r.json()) == 1


def test_api_create_duplicate_409(client: TestClient) -> None:
    client.post("/api/webhooks", json=_sample())
    r = client.post("/api/webhooks", json=_sample())
    assert r.status_code == 409


def test_api_update_with_extra_none_normalizes_to_empty_dict(
    client: TestClient,
) -> None:
    """回归: PATCH extra: None 之前会 500 (Pydantic 拒绝 None as dict).

    修复后应返回 200, extra 规范化为 {}.
    """
    client.post("/api/webhooks", json=_sample())
    r = client.put("/api/webhooks/wh-1", json={"extra": None})
    assert r.status_code == 200, r.text
    assert r.json()["extra"] == {}


def test_api_update_404(client: TestClient) -> None:
    r = client.put("/api/webhooks/missing", json={"name": "x"})
    assert r.status_code == 404


def test_api_update_rejects_extra_field_via_pydantic(
    client: TestClient,
) -> None:
    """Pydantic extra='forbid' 必须在 HTTP 层挡住未知字段, 不让落到 manager."""
    client.post("/api/webhooks", json=_sample())
    r = client.put("/api/webhooks/wh-1", json={"unknown_field": "x"})
    assert r.status_code == 422


def test_api_delete_204_then_404(client: TestClient) -> None:
    client.post("/api/webhooks", json=_sample())
    r = client.delete("/api/webhooks/wh-1")
    assert r.status_code == 204
    r = client.delete("/api/webhooks/wh-1")
    assert r.status_code == 404
