"""Webhook 配置存储: JSON 文件读写 (无数据库).

数据文件位于 data/webhooks.json, 结构:
    {"webhooks": [ {webhook 配置}, ... ]}

单个 webhook 的字段与前端契约保持一致:
    id, name, platform, url, secret, extra, enabled
"""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any

from loguru import logger

# 项目根目录: config.py -> webhook -> src -> 项目根
ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"


class ConfigManager:
    """webhooks.json 的读取与写入.

    线程安全: 所有操作经 self._lock 串行化.
    写入采用"临时文件 + 原子替换", 避免写一半损坏数据.
    """

    def __init__(self, data_dir: str | Path | None = None) -> None:
        self._file = (Path(data_dir) if data_dir else DATA_DIR) / "webhooks.json"
        self._lock = threading.Lock()

    # ---- 核心读写 ----

    def load(self) -> list[dict[str, Any]]:
        """读取全部 webhook 配置; 文件不存在或损坏时返回空列表."""
        with self._lock:
            if not self._file.exists():
                logger.debug("webhook 配置文件不存在, 返回空列表: {}", self._file)
                return []
            try:
                raw = json.loads(self._file.read_text(encoding="utf-8"))
                webhooks = raw.get("webhooks", []) if isinstance(raw, dict) else []
                logger.debug("已加载 {} 条 webhook 配置", len(webhooks))
                return webhooks
            except json.JSONDecodeError:
                logger.error("webhook 配置文件损坏, 返回空列表: {}", self._file)
                return []

    def save(self, webhooks: list[dict[str, Any]]) -> None:
        """整体写回全部 webhook 配置."""
        with self._lock:
            self._file.parent.mkdir(parents=True, exist_ok=True)
            tmp = self._file.with_name(self._file.name + ".tmp")
            tmp.write_text(
                json.dumps({"webhooks": webhooks}, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            tmp.replace(self._file)
            logger.debug("已保存 {} 条 webhook 配置 -> {}", len(webhooks), self._file)
