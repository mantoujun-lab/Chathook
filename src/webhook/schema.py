"""Webhook 配置相关 Pydantic schema.

定义 REST API 层使用的 request/response 模型, 获得:
  - 自动字段校验 (FastAPI 422 错误 + 清晰定位)
  - OpenAPI 文档 (http://localhost:8000/docs)
  - 前端可通过 openapi-typescript 生成类型契约

Pydantic 使用 v2 语法 (from __future__ 开启的 PEP 604 联合 / model_config 等).
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class PlatformType(str, Enum):
    """支持的出站 Webhook 平台."""

    FEISHU = "feishu"
    DINGTALK = "dingtalk"
    CUSTOM = "custom"


# -------------------- 基础模型 --------------------

_EXTRA_DESCRIPTION = (
    "各平台自定义字段: 飞书/DingTalk 用于签名开关、自定义 webhook "
    "用于自定义 headers / 内容类型等"
)


class WebhookConfigBase(BaseModel):
    """不含 id 的可写字段, 被 create/update 复用."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1, max_length=128, description="显示名称")
    platform: PlatformType = Field(..., description="目标平台枚举")
    url: str = Field(
        ...,
        min_length=8,
        max_length=1024,
        pattern=r"^https?://",
        description="Webhook URL, 必须 http/https 开头",
    )
    secret: str | None = Field(
        default=None,
        description="签名密钥, 无签名校验时传 null",
    )
    extra: dict[str, Any] = Field(
        default_factory=dict,
        description=_EXTRA_DESCRIPTION,
    )
    enabled: bool = Field(default=True, description="是否启用")


class WebhookConfig(WebhookConfigBase):
    """出参用完整配置, 包含唯一 id."""

    model_config = ConfigDict(from_attributes=True, extra="ignore")

    id: str = Field(..., min_length=1, max_length=128, description="配置唯一 ID")


# -------------------- 请求模型 --------------------

class WebhookCreate(WebhookConfigBase):
    """新增配置入参.

    除继承自 WebhookConfigBase 的字段外, 必须提供唯一 id.
    """

    id: str = Field(..., min_length=1, max_length=128, description="配置唯一 ID")


class WebhookUpdate(BaseModel):
    """更新配置入参.

    所有字段可选; id 不允许通过更新修改 (由路径参数指定).
    extra 提供时会**整体替换**存储中的 extra 对象 (不做 key 级增量 merge),
    若需增量合并请前端先 GET 再 PUT 回完整 extra.
    """

    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=128)
    platform: PlatformType | None = None
    url: str | None = Field(
        default=None,
        min_length=8,
        max_length=1024,
        pattern=r"^https?://",
    )
    secret: str | None = Field(default=None)
    extra: dict[str, Any] | None = Field(default=None, description=_EXTRA_DESCRIPTION)
    enabled: bool | None = None


# -------------------- 列表容器模型 --------------------

WebhookConfigList = list[WebhookConfig]
"""列表响应模型别名; FastAPI list[WebhookConfig] 直接作为 response_model 使用."""

__all__ = [
    "PlatformType",
    "WebhookConfig",
    "WebhookConfigBase",
    "WebhookConfigList",
    "WebhookCreate",
    "WebhookUpdate",
]
