"""Webhook HTTP API: FastAPI router for webhook config CRUD."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from .services import WebhookManager

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])

_manager = WebhookManager()


@router.get("", response_model=list[dict[str, Any]])
def list_webhooks() -> list[dict[str, Any]]:
    """列出全部 webhook 配置."""
    return _manager.list()


@router.get("/{webhook_id}", response_model=dict[str, Any])
def get_webhook(webhook_id: str) -> dict[str, Any]:
    """按 ID 获取单个 webhook."""
    webhook = _manager.get(webhook_id)
    if webhook is None:
        raise HTTPException(status_code=404, detail="Webhook not found")
    return webhook


@router.post("", status_code=201, response_model=dict[str, Any])
def create_webhook(payload: dict[str, Any]) -> dict[str, Any]:
    """新增 webhook; ID 重复返回 409."""
    try:
        return _manager.create(payload)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except KeyError as exc:
        raise HTTPException(status_code=422, detail=f"Missing field: {exc}") from exc


@router.put("/{webhook_id}", response_model=dict[str, Any])
def update_webhook(webhook_id: str, patch: dict[str, Any]) -> dict[str, Any]:
    """按 ID 更新 webhook."""
    webhook = _manager.update(webhook_id, patch)
    if webhook is None:
        raise HTTPException(status_code=404, detail="Webhook not found")
    return webhook


@router.delete("/{webhook_id}", status_code=204)
def delete_webhook(webhook_id: str) -> None:
    """按 ID 删除 webhook."""
    if not _manager.delete(webhook_id):
        raise HTTPException(status_code=404, detail="Webhook not found")
