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

app = FastAPI(title="Chathook", version="1.0.0")
app.include_router(webhook_router)


@app.get("/health")
def health() -> dict[str, str]:
    """健康检查."""
    return {"status": "ok"}

# 项目根目录 (即本文件所在目录)
ROOT = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(ROOT, "dashboard")

# 显式使用 argv 列表 + shell=False:
#   - 避免 shell=True 引入的命令注入面 (即使本工具只本地开发使用)
#   - 子进程非零退出码通过 returncode 显式处理, 不依赖 shell 行为
#   - 跨平台: uv 与 npm 在 PATH 中均注册了可执行文件 (Windows 上是 uv.exe /
#     npm.cmd), 解析工作交给 CreateProcess / execvp, 不再走 cmd.exe/bash.
_BACKEND_ARGV: tuple[str, ...] = (
    "uv",
    "run",
    "uvicorn",
    "main:app",
    "--reload",
    "--host",
    "0.0.0.0",
    "--port",
    "8000",
)
# npm 在 Windows 上需要通过 npm.cmd 调用 (uv/shutil.which 能处理),
# 但 subprocess shell=False 列表传 "npm" 即可: PATHEXT 会让 CreateProcess
# 自动匹配到 npm.cmd.
_FRONTEND_ARGV: tuple[str, ...] = ("npm", "run", "dev")

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
    """并行启动后端 (uvicorn) 与前端 (Nuxt), 任一退出则整体停止.

    与旧实现不同: 使用列表 argv + shell=False, 并在检测到非预期退出时
    把子进程退出码透传给 sys.exit, 使失败显式化.
    """
    backend_cmd_str = " ".join(_BACKEND_ARGV)
    frontend_cmd_str = " ".join(_FRONTEND_ARGV)
    print("== Chathook 一键启动 ==")
    print(f"后端: {backend_cmd_str}")
    print(f"前端: cd {FRONTEND_DIR} && {frontend_cmd_str}")
    print("按 Ctrl+C 可同时关闭两个服务\n")

    # shell=False + argv 列表; 不使用环境变量继承 PATH 即可
    procs = [
        subprocess.Popen(
            _BACKEND_ARGV,
            cwd=ROOT,
            shell=False,
            text=True,
        ),
        subprocess.Popen(
            _FRONTEND_ARGV,
            cwd=FRONTEND_DIR,
            shell=False,
            text=True,
        ),
    ]

    first_exit_code = 0
    first_exited_label: str | None = None

    try:
        # 任一子进程退出则整体停止
        while True:
            for label, proc in (("backend", procs[0]), ("frontend", procs[1])):
                rc = proc.poll()
                if rc is not None:
                    first_exit_code = rc
                    first_exited_label = label
                    print(
                        f"{label} 进程已退出 (code={rc}), 停止全部服务..."
                    )
                    raise KeyboardInterrupt
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\n正在关闭服务...")
    finally:
        for proc in procs:
            if proc.poll() is None:
                proc.terminate()
        # 等待优雅退出, 超时则强制结束
        for label, proc in (("backend", procs[0]), ("frontend", procs[1])):
            try:
                rc = proc.wait(timeout=5)
                # 如果有非零退出码但 first_exit_code 还没记录下来, 保留下来
                if rc != 0 and first_exited_label is None:
                    first_exit_code = rc
                    first_exited_label = label
            except subprocess.TimeoutExpired:
                proc.kill()
                try:
                    proc.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    pass
                if first_exited_label is None:
                    first_exit_code = -9
                    first_exited_label = label
        # 清理残留的 __pycache__ 字节码缓存
        clean_pycache(ROOT)

    if first_exit_code != 0:
        print(
            f"有进程异常退出 ({first_exited_label}, code={first_exit_code})"
        )
    else:
        print("已全部关闭.")
    return first_exit_code


if __name__ == "__main__":
    sys.exit(run_dev())
