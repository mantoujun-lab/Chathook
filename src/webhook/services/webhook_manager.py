"""Webhook 配置业务管理：增删改查（CRUD）。

基于 ConfigManager 的 JSON 存储，操作纯 dict 数据。
webhook 字段契约与前端一致：id, name, platform, url, secret, extra, enabled
"""

from __future__ import annotations

from typing import Any

from loguru import logger

from ..config import ConfigManager


class WebhookManager:
    """webhook 配置的增删改查。"""

    def __init__(self, config: ConfigManager | None = None) -> None:
        self._config = config or ConfigManager()

    def list(self) -> list[dict[str, Any]]:
        """返回全部 webhook 配置。"""
        return self._config.load()

    def get(self, webhook_id: str) -> dict[str, Any] | None:
        """按 ID 查找单个 webhook；不存在返回 None。"""
        return next(
            (w for w in self._config.load() if w.get("id") == webhook_id), None
        )

    def create(self, webhook: dict[str, Any]) -> dict[str, Any]:
        """新增 webhook；ID 已存在时抛 ValueError。"""
        webhooks = self._config.load()
        if any(w.get("id") == webhook["id"] for w in webhooks):
            logger.warning("创建失败，ID 已存在: {}", webhook["id"])
            raise ValueError(f'Webhook ID 已存在: {webhook["id"]}')
        webhooks.append(webhook)
        self._config.save(webhooks)
        logger.info("已新增 webhook: {} ({})", webhook["id"], webhook["name"])
        return webhook

    def update(self, webhook_id: str, patch: dict[str, Any]) -> dict[str, Any] | None:
        """按 ID 更新字段；ID 不可变更；不存在返回 None。"""
        patch = dict(patch)
        patch.pop("id", None)  # 禁止通过 update 修改 ID
        webhooks = self._config.load()
        for w in webhooks:
            if w.get("id") == webhook_id:
                w.update(patch)
                self._config.save(webhooks)
                logger.info("已更新 webhook: {}", webhook_id)
                return w
        logger.warning("更新失败，未找到 webhook: {}", webhook_id)
        return None

    def delete(self, webhook_id: str) -> bool:
        """按 ID 删除；删除成功返回 True，不存在返回 False。"""
        webhooks = self._config.load()
        remaining = [w for w in webhooks if w.get("id") != webhook_id]
        if len(remaining) == len(webhooks):
            logger.warning("删除失败，未找到 webhook: {}", webhook_id)
            return False
        self._config.save(remaining)
        logger.info("已删除 webhook: {}", webhook_id)
        return True
