"""Chathook entry point.

Single-process launcher: builds the Nuxt frontend on demand and serves
both the static dashboard and the FastAPI backend on a single port.

Usage:
    uv run python main.py
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.responses import FileResponse
from starlette.staticfiles import StaticFiles

from src.webhook.api import router as webhook_router

ROOT = Path(__file__).resolve().parent
FRONTEND_DIR = ROOT / "dashboard"
OUTPUT_DIR = FRONTEND_DIR / ".output" / "public"
INDEX_FILE = OUTPUT_DIR / "index.html"

HOST = "127.0.0.1"
PORT = 8000

app = FastAPI(title="Chathook", version="1.1.0")
app.include_router(webhook_router)


@app.get("/health", include_in_schema=False)
def health() -> dict[str, str]:
    return {"status": "ok"}


def _mount_static(app: FastAPI) -> None:
    if (OUTPUT_DIR / "_nuxt").is_dir():
        app.mount(
            "/_nuxt",
            StaticFiles(directory=str(OUTPUT_DIR / "_nuxt")),
            name="nuxt-assets",
        )

    @app.get("/{full_path:path}", include_in_schema=False)
    def spa_fallback(full_path: str) -> FileResponse:
        candidate = (OUTPUT_DIR / full_path).resolve()
        try:
            candidate.relative_to(OUTPUT_DIR.resolve())
        except ValueError:
            candidate = INDEX_FILE
        if candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(INDEX_FILE)


_mount_static(app)


def _resolve_executable(name: str) -> str:
    resolved = shutil.which(name)
    if resolved is None:
        raise FileNotFoundError(
            f"找不到可执行文件: {name!r}. 请确认它已安装并在 PATH 中."
        )
    return resolved


def _newest_mtime(root: Path) -> float:
    if not root.exists():
        return 0.0
    latest = root.stat().st_mtime
    for p in root.rglob("*"):
        if p.is_file():
            latest = max(latest, p.stat().st_mtime)
    return latest


def _needs_rebuild() -> bool:
    if not INDEX_FILE.is_file():
        return True
    pkg = FRONTEND_DIR / "package.json"
    if not (FRONTEND_DIR / "node_modules").is_dir():
        return True
    if pkg.is_file() and pkg.stat().st_mtime > _newest_mtime(OUTPUT_DIR):
        return True
    return False


def _run(argv: list[str], cwd: Path) -> None:
    print(f"$ {' '.join(argv)}  (cwd={cwd})")
    result = subprocess.run(argv, cwd=cwd, shell=False)
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
    if not (FRONTEND_DIR / "node_modules").is_dir():
        _run([npm, "install"], FRONTEND_DIR)
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
