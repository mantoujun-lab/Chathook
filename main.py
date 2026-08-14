"""Chathook 后端入口: FastAPI 应用 + 一键启动.

单独启动后端 (开发):
    uv run uvicorn main:app --reload

一键启动后端 + 前端 (等效迁移前的 start.py):
    uv run python main.py
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time

from fastapi import FastAPI

from src.webhook.api import router as webhook_router

app = FastAPI(title="Chathook", version="0.1.0")
app.include_router(webhook_router)


@app.get("/health")
def health() -> dict[str, str]:
    """健康检查."""
    return {"status": "ok"}

# 项目根目录 (即本文件所在目录)
ROOT = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(ROOT, "dashboard")

BACKEND_CMD = "uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000"
FRONTEND_CMD = "npm run dev"

# 清理时跳过这些目录 (虚拟环境/依赖/版本库)
_SKIP_DIRS = {".git", ".venv", "venv", "node_modules"}


def clean_pycache(root: str) -> None:
    """递归清理 root 下的所有 __pycache__ 目录."""
    removed = 0
    for dirpath, dirnames, _ in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in _SKIP_DIRS]
        if "__pycache__" in dirnames:
            shutil.rmtree(os.path.join(dirpath, "__pycache__"), ignore_errors=True)
            removed += 1
    if removed:
        print(f"已清理 {removed} 个 __pycache__ 目录")


def run_dev() -> int:
    """并行启动后端 (uvicorn) 与前端 (Nuxt), 任一退出则整体停止."""
    print("== Chathook 一键启动 ==")
    print(f"后端: {BACKEND_CMD}")
    print(f"前端: cd {FRONTEND_DIR} && {FRONTEND_CMD}")
    print("按 Ctrl+C 可同时关闭两个服务\n")

    # shell=True 可同时兼容 Windows 的 cmd 与 POSIX 的 sh
    procs = [
        subprocess.Popen(BACKEND_CMD, cwd=ROOT, shell=True),
        subprocess.Popen(FRONTEND_CMD, cwd=FRONTEND_DIR, shell=True),
    ]

    try:
        # 任一子进程退出则整体停止
        while True:
            for proc in procs:
                if proc.poll() is not None:
                    print("有进程已退出, 停止全部服务...")
                    raise KeyboardInterrupt
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\n正在关闭服务...")
    finally:
        for proc in procs:
            if proc.poll() is None:
                proc.terminate()
        # 等待优雅退出, 超时则强制结束
        for proc in procs:
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
        # 清理残留的 __pycache__ 字节码缓存
        clean_pycache(ROOT)

    print("已全部关闭.")
    return 0


if __name__ == "__main__":
    sys.exit(run_dev())
