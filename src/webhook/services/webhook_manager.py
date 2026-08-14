"""Webhook 配置业务管理: 增删改查 (CRUD).

基于 ConfigManager 的 JSON 存储, 操作纯 dict 数据.
webhook 字段契约与前端一致: id, name, platform, url, secret, extra, enabled

异常传播约定:
  - ConfigManager.load/save 抛的 ConfigCorruptedError 原样透出到 API 层,
    返回 500 并告知用户需人工修复, 避免用空配置覆盖损坏文件.
"""

from __future__ import annotations

from typing import Any

from loguru import logger

from ..config import ConfigCorruptedError, ConfigManager


__all__ = ["WebhookManager", "ConfigCorruptedError"]


# 允许通过 update() 写入磁盘的字段白名单, 与 WebhookConfig schema 保持一致.
# Pydantic schema (WebhookUpdate) 在 HTTP 入口已做第一道限制; 此处再做一层
# 存储层兜底, 避免内部调用方绕过 schema 写入任意字段导致 JSON schema 漂移.
_ALLOWED_UPDATE_KEYS: frozenset[str] = frozenset(
    {"name", "platform", "url", "secret", "extra", "enabled"}
)


class WebhookManager:
    """webhook 配置的增删改查."""

    def __init__(self, config: ConfigManager | None = None) -> None:
        self._config = config or ConfigManager()

    def list(self) -> list[dict[str, Any]]:
        """返回全部 webhook 配置."""
        return self._config.load()

    def get(self, webhook_id: str) -> dict[str, Any] | None:
        """按 ID 查找单个 webhook; 不存在返回 None."""
        return next(
            (w for w in self._config.load() if w.get("id") == webhook_id), None
        )

    def create(self, webhook: dict[str, Any]) -> dict[str, Any]:
        """新增 webhook; ID 已存在时抛 ValueError."""
        webhooks = self._config.load()
        if any(w.get("id") == webhook["id"] for w in webhooks):
            logger.warning("创建失败, ID 已存在: {}", webhook["id"])
            raise ValueError(f"Webhook ID 已存在: {webhook['id']}")
        webhooks.append(webhook)
        self._config.save(webhooks)
        logger.info("已新增 webhook: {} ({})", webhook["id"], webhook["name"])
        return webhook

    def update(self, webhook_id: str, patch: dict[str, Any]) -> dict[str, Any] | None:
        """按 ID 更新字段; 仅允许 _ALLOWED_UPDATE_KEYS 白名单中的字段.

        - 禁止通过 update 修改 "id" (白名单本身也不包含)
        - 传入未知键会直接抛 KeyError, 而不是静默丢弃, 以便调用方尽快发现
          契约不一致 (内部服务调用绕过 Pydantic schema 的场景)
        - 返回 None 表示未找到目标 ID
        """
        patch = dict(patch)
        # 先整体校验白名单: 任何不在 _ALLOWED_UPDATE_KEYS 中的键都视为调用错误
        unknown = [k for k in patch.keys() if k not in _ALLOWED_UPDATE_KEYS]
        if unknown:
            raise KeyError(
                f"Webhook update 不允许修改字段: {unknown!r}; "
                f"允许的键: {sorted(_ALLOWED_UPDATE_KEYS)}"
            )

        webhooks = self._config.load()
        for w in webhooks:
            if w.get("id") == webhook_id:
                w.update(patch)
                self._config.save(webhooks)
                logger.info("已更新 webhook: {}", webhook_id)
                return w
        logger.warning("更新失败, 未找到 webhook: {}", webhook_id)
        return None

    def delete(self, webhook_id: str) -> bool:
        """按 ID 删除; 删除成功返回 True, 不存在返回 False."""
        webhooks = self._config.load()
        remaining = [w for w in webhooks if w.get("id") != webhook_id]
        if len(remaining) == len(webhooks):
            logger.warning("删除失败, 未找到 webhook: {}", webhook_id)
            return False
        self._config.save(remaining)
        logger.info("已删除 webhook: {}", webhook_id)
        return True
