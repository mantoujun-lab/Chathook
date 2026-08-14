"""Webhook 配置存储: JSON 文件读写 (无数据库).

数据文件位于 data/webhooks.json, 结构:
    {"webhooks": [ {webhook 配置}, ... ]}

单个 webhook 的字段与前端契约保持一致:
    id, name, platform, url, secret, extra, enabled
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

from loguru import logger

# 项目根目录: config.py -> webhook -> src -> 项目根
ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"


class ConfigCorruptedError(Exception):
    """webhooks.json JSON 损坏; 保存会被拦截以避免覆盖损坏文件."""


@contextmanager
def _file_lock(path: Path) -> Iterator[None]:
    """跨进程文件锁上下文.

    Windows 使用 msvcrt.locking 对独立 .lock 文件做独占锁;
    POSIX 使用 fcntl.flock. 锁文件位于数据文件旁, 进程崩溃后会被 OS 释放.
    """
    lock_path = path.with_suffix(path.suffix + ".lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    # 使用二进制模式避免额外的换行符转换
    with lock_path.open("ab+") as fh:
        if sys.platform == "win32":
            import msvcrt

            # LK_LOCK = 2 (阻塞式独占锁), 锁定从文件头开始 1 字节
            fh.seek(0)
            try:
                # 锁文件保持小于 1 字节也能加锁, 但写入一个占位避免零文件奇怪行为
                if not os.fstat(fh.fileno()).st_size:
                    fh.write(b".")
                    fh.flush()
                msvcrt.locking(fh.fileno(), msvcrt.LK_LOCK, 1)
            except OSError:
                raise
            try:
                yield
            finally:
                fh.seek(0)
                try:
                    msvcrt.locking(fh.fileno(), msvcrt.LK_UNLCK, 1)
                except OSError:
                    pass
        else:
            import fcntl

            try:
                fcntl.flock(fh, fcntl.LOCK_EX)
            except OSError:
                raise
            try:
                yield
            finally:
                try:
                    fcntl.flock(fh, fcntl.LOCK_UN)
                except OSError:
                    pass


class ConfigManager:
    """webhooks.json 的读取与写入.

    并发安全:
      - 同进程内通过 threading.Lock 串行化
      - 跨进程/跨容器通过独立 .lock 文件的文件锁 (fcntl / msvcrt) 保护
    写入采用"临时文件 + 原子替换", 避免写一半损坏数据.
    损坏保护:
      - load() 解析失败时抛 ConfigCorruptedError (不再返回空列表) 并把损坏文件
        备份为 webhooks.json.corrupted.<timestamp>; 后续 save() 会被拦截避免覆盖.
    """

    def __init__(self, data_dir: str | Path | None = None) -> None:
        self._file = (Path(data_dir) if data_dir else DATA_DIR) / "webhooks.json"
        self._thread_lock = threading.Lock()
        self._corrupted = False

    # ---- 损坏标记与备份 ----

    def _mark_corrupted_and_backup(self) -> None:
        """把当前损坏文件复制一份备份, 并标记 corrupted 状态以拦截 save()."""
        import time

        backup = self._file.with_name(
            f"{self._file.name}.corrupted.{int(time.time())}"
        )
        try:
            backup.write_bytes(self._file.read_bytes())
            logger.error(
                "webhook 配置文件损坏, 已备份为 {}; 拒绝自动保存", backup
            )
        except OSError as exc:
            logger.error(
                "webhook 配置文件损坏且无法备份 ({}), 仍将拒绝保存", exc
            )
        self._corrupted = True

    # ---- 核心读写 ----

    def load(self) -> list[dict[str, Any]]:
        """读取全部 webhook 配置.

        - 文件不存在: 返回空列表 (首次运行状态)
        - 文件存在且 JSON 顶层为 dict, 含合法 "webhooks" 数组: 返回该列表
        - JSON 语法错误 / 顶层不是 dict (例如顶层 list / 数字 / 字符串):
          视为格式不符合预期 -> 备份 -> 抛 ConfigCorruptedError.
          这样不会用 [] 静默替换非预期的 JSON 结构, 避免后续 save()
          覆盖掉原本可能可修复的数据 (比如老版本存储的顶层 list).
        """
        with self._thread_lock, _file_lock(self._file):
            if not self._file.exists():
                logger.debug("webhook 配置文件不存在, 返回空列表: {}", self._file)
                self._corrupted = False
                return []
            try:
                raw = json.loads(self._file.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                logger.error("webhook 配置文件 JSON 语法错误: {}", self._file)
                self._mark_corrupted_and_backup()
                raise ConfigCorruptedError(
                    f"webhook 配置文件 JSON 语法错误: {self._file}; 已备份, 未覆盖"
                ) from exc

            # 顶层非 dict: 例如顶层 list / 字符串 / 数字等"解析成功但结构错误"
            # 的情况, 也视为损坏并拦截, 不再走 isinstance(raw, dict) ? [] : xxx
            # 的静默降级分支.
            if not isinstance(raw, dict):
                logger.error(
                    "webhook 配置文件顶层 JSON 不是预期的 dict, 实际为 {}: {}",
                    type(raw).__name__,
                    self._file,
                )
                self._mark_corrupted_and_backup()
                raise ConfigCorruptedError(
                    f"webhook 配置文件顶层 JSON 必须是 {{'webhooks': [...]}}"
                    f" 格式, 实际为 {type(raw).__name__}; 已备份, 未覆盖"
                )

            webhooks = raw.get("webhooks", [])
            if not isinstance(webhooks, list):
                logger.error(
                    "webhook 配置文件 'webhooks' 字段不是 list, 实际为 {}: {}",
                    type(webhooks).__name__,
                    self._file,
                )
                self._mark_corrupted_and_backup()
                raise ConfigCorruptedError(
                    f"webhook 配置文件 'webhooks' 字段必须是数组, "
                    f"实际为 {type(webhooks).__name__}; 已备份, 未覆盖"
                )
            logger.debug("已加载 {} 条 webhook 配置", len(webhooks))
            self._corrupted = False
            return webhooks

    def save(self, webhooks: list[dict[str, Any]]) -> None:
        """整体写回全部 webhook 配置.

        若文件此前被判定为损坏 (load() 抛过 ConfigCorruptedError 且未被人工修复后
        再次 load 成功), 则拒绝保存以避免覆盖损坏文件.
        """
        with self._thread_lock, _file_lock(self._file):
            if self._corrupted:
                raise ConfigCorruptedError(
                    f"webhook 配置文件已标记为损坏, 拒绝保存: {self._file}. "
                    "请人工修复或移除备份后再保存."
                )
            self._file.parent.mkdir(parents=True, exist_ok=True)
            # 原子写入: 先写到同目录临时文件, 再 os.replace (Windows 也支持)
            fd, tmp_path = tempfile.mkstemp(
                prefix=self._file.name + ".",
                suffix=".tmp",
                dir=str(self._file.parent),
            )
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as tmp:
                    tmp.write(
                        json.dumps(
                            {"webhooks": webhooks},
                            ensure_ascii=False,
                            indent=2,
                        )
                    )
                    tmp.flush()
                    os.fsync(tmp.fileno())
                os.replace(tmp_path, self._file)
            except Exception:
                # 任何异常都尽量清理残留临时文件
                try:
                    if os.path.exists(tmp_path):
                        os.unlink(tmp_path)
                except OSError:
                    pass
                raise
            logger.debug("已保存 {} 条 webhook 配置 -> {}", len(webhooks), self._file)
