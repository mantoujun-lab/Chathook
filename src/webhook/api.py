"""Webhook HTTP API: FastAPI router for webhook config CRUD.

使用 schema.py 中定义的 Pydantic 模型作为入参和出参, 获得:
  - 自动字段校验 (FastAPI 422)
  - 完整 OpenAPI schema
  - ConfigCorruptedError 统一映射为 500, 阻止损坏配置被空列表覆盖
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from .config import ConfigCorruptedError
from .schema import WebhookConfig, WebhookCreate, WebhookUpdate
from .services import WebhookManager

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])

_manager = WebhookManager()


def _raise_on_corrupted(exc: ConfigCorruptedError) -> None:
    """ConfigCorruptedError 映射到 500, 告诉用户配置损坏需人工修复."""
    raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("", response_model=list[WebhookConfig])
def list_webhooks() -> list[WebhookConfig]:
    """列出全部 webhook 配置."""
    try:
        raw = _manager.list()
    except ConfigCorruptedError as exc:
        _raise_on_corrupted(exc)
    return [WebhookConfig.model_validate(w) for w in raw]


@router.get("/{webhook_id}", response_model=WebhookConfig)
def get_webhook(webhook_id: str) -> WebhookConfig:
    """按 ID 获取单个 webhook."""
    try:
        webhook = _manager.get(webhook_id)
    except ConfigCorruptedError as exc:
        _raise_on_corrupted(exc)
    if webhook is None:
        raise HTTPException(status_code=404, detail="Webhook not found")
    return WebhookConfig.model_validate(webhook)


@router.post("", status_code=201, response_model=WebhookConfig)
def create_webhook(payload: WebhookCreate) -> WebhookConfig:
    """新增 webhook; ID 重复返回 409."""
    try:
        created = _manager.create(payload.model_dump())
    except ConfigCorruptedError as exc:
        _raise_on_corrupted(exc)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return WebhookConfig.model_validate(created)


@router.put("/{webhook_id}", response_model=WebhookConfig)
def update_webhook(webhook_id: str, patch: WebhookUpdate) -> WebhookConfig:
    """按 ID 更新 webhook.

    Pydantic 模型已禁止 extra="forbid", 传未知字段会自动返回 422.
    """
    patch_dict = patch.model_dump(exclude_unset=True)
    try:
        webhook = _manager.update(webhook_id, patch_dict)
    except ConfigCorruptedError as exc:
        _raise_on_corrupted(exc)
    if webhook is None:
        raise HTTPException(status_code=404, detail="Webhook not found")
    return WebhookConfig.model_validate(webhook)


@router.delete("/{webhook_id}", status_code=204)
def delete_webhook(webhook_id: str) -> None:
    """按 ID 删除 webhook."""
    try:
        deleted = _manager.delete(webhook_id)
    except ConfigCorruptedError as exc:
        _raise_on_corrupted(exc)
    if not deleted:
        raise HTTPException(status_code=404, detail="Webhook not found")
