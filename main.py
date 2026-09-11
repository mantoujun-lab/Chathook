"""Chathook entry point.

Single-process launcher: builds the Nuxt frontend on demand and serves
both the static dashboard and the FastAPI backend on a single port.

Usage:
    uv run python main.py
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from starlette.staticfiles import StaticFiles

from src.webhook.api import router as webhook_router

ROOT = Path(__file__).resolve().parent
FRONTEND_DIR = ROOT / "dashboard"
OUTPUT_DIR = FRONTEND_DIR / ".output" / "public"
INDEX_FILE = OUTPUT_DIR / "index.html"

HOST = "127.0.0.1"
PORT = 8000

# 触发前端重建的输入: 源码目录 + 构建配置 + 依赖清单
_FRONTEND_INPUTS = ("app", "nuxt.config.ts", "package.json", "package-lock.json")
# npm ci 后写入的依赖安装标记, 用于判断 node_modules 是否与依赖清单一致
_INSTALL_MARKER = FRONTEND_DIR / "node_modules" / ".package-lock.json"

app = FastAPI(title="Chathook", version="1.1.0")
app.include_router(webhook_router)


@app.get("/health", include_in_schema=False)
def health() -> dict[str, str]:
    return {"status": "ok"}


def _resolve_spa_file(full_path: str) -> Path:
    """把前端路由解析为产物文件, 越界或缺失时回退到 index.html.

    先用 ``realpath`` 规范化 (消除 ``..`` 并解析符号链接), 再校验结果仍位于
    产物目录内; 只有通过前缀检查的路径才会被访问, 避免目录穿越.
    """
    root = os.path.realpath(OUTPUT_DIR)
    candidate = os.path.realpath(os.path.join(root, full_path))
    if not candidate.startswith(root + os.sep):
        return INDEX_FILE
    return Path(candidate) if os.path.isfile(candidate) else INDEX_FILE


def _mount_static(app: FastAPI) -> None:
    if (OUTPUT_DIR / "_nuxt").is_dir():
        app.mount(
            "/_nuxt",
            StaticFiles(directory=str(OUTPUT_DIR / "_nuxt")),
            name="nuxt-assets",
        )

    @app.get("/{full_path:path}", include_in_schema=False)
    def spa_fallback(full_path: str) -> FileResponse:
        # 未知的 API 路径应返回 404, 而不是把 HTML 面板当作成功响应返回
        if full_path == "api" or full_path.startswith("api/"):
            raise HTTPException(status_code=404)
        # 前端产物缺失时 (例如只启动了后端), 未匹配的 GET 返回 404 而非 500
        if not INDEX_FILE.is_file():
            raise HTTPException(status_code=404)
        return FileResponse(_resolve_spa_file(full_path))


_mount_static(app)


def _resolve_executable(name: str) -> str:
    resolved = shutil.which(name)
    if resolved is None:
        raise FileNotFoundError(
            f"找不到可执行文件: {name!r}. 请确认它已安装并在 PATH 中."
        )
    return resolved


def _newest_mtime(path: Path) -> float:
    if not path.exists():
        return 0.0
    if path.is_file():
        return path.stat().st_mtime
    latest = 0.0
    for child in path.rglob("*"):
        if child.is_file():
            latest = max(latest, child.stat().st_mtime)
    return latest


def _frontend_inputs_mtime() -> float:
    return max(_newest_mtime(FRONTEND_DIR / name) for name in _FRONTEND_INPUTS)


def _needs_rebuild() -> bool:
    if not INDEX_FILE.is_file():
        return True
    return _frontend_inputs_mtime() > _newest_mtime(OUTPUT_DIR)


def _needs_install() -> bool:
    if not _INSTALL_MARKER.is_file():
        return True
    deps_mtime = max(
        _newest_mtime(FRONTEND_DIR / "package.json"),
        _newest_mtime(FRONTEND_DIR / "package-lock.json"),
    )
    return deps_mtime > _INSTALL_MARKER.stat().st_mtime


def _run(argv: list[str], cwd: Path) -> None:
    print(f"$ {' '.join(argv)}  (cwd={cwd})")
    # argv 只由静态参数与 shutil.which 解析出的绝对路径组成, 无外部输入,
    # 且 shell=False, 不存在命令注入; nosemgrep 抑制审计规则的误报.
    result = subprocess.run(argv, cwd=cwd, shell=False)  # nosemgrep
    if result.returncode != 0:
        raise RuntimeError(
            f"命令失败 (code={result.returncode}): {' '.join(argv)}"
        )


def _ensure_frontend() -> None:
    if not _needs_rebuild():
        print(f"前端产物已是最新, 复用 {OUTPUT_DIR}")
        return
    print("未检测到可用前端产物, 开始构建...")
    npm = _resolve_executable("npm")
    if _needs_install():
        _run([npm, "ci"], FRONTEND_DIR)
    _run([npm, "run", "generate"], FRONTEND_DIR)


def _run_server() -> int:
    print("== Chathook 启动 ==")
    print(f"监听: http://{HOST}:{PORT}")
    print("按 Ctrl+C 可关闭服务")
    uvicorn.run("main:app", host=HOST, port=PORT, reload=False, log_level="info")
    return 0


if __name__ == "__main__":
    try:
        _ensure_frontend()
    except (FileNotFoundError, RuntimeError) as exc:
        print(f"前端构建失败: {exc}")
        sys.exit(1)
    sys.exit(_run_server())
