"""冒烟测试: 验证 FastAPI 应用可正常启动, 核心路由可达."""

from __future__ import annotations

from fastapi.testclient import TestClient

from main import app


def test_health() -> None:
    """健康检查接口应返回 200 与 ok 状态."""
    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
