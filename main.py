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

# 使用 argv 列表 + shell=False:
#   - 避免 shell=True 引入的命令注入面 (即使本工具只本地开发使用)
#   - 子进程非零退出码通过 returncode 显式处理, 不依赖 shell 行为
#   - 实际可执行文件通过 _resolve_executable() 解析 (Windows 上 npm 是
#     npm.cmd, uv 是 uv.exe), 保证 subprocess 在 shell=False 下也能启动.
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


def _resolve_executable(name: str) -> str:
    """在 Windows 上把 "npm" / "uv" 解析为具体的可执行文件路径.

    subprocess.Popen + shell=False 在 Windows 下不会自动扩展 PATHEXT,
    因此直接传 "npm" 会报 FileNotFoundError. 使用 shutil.which 能拿到
    真实的 .exe / .cmd 文件, 同时保留 shell=False 的安全性.
    """
    resolved = shutil.which(name)
    if resolved is None:
        # 给一个清晰的错误, 避免在 CreateProcess 深处才失败
        raise FileNotFoundError(
            f"找不到可执行文件: {name!r}. 请确认它已安装并在 PATH 中."
        )
    return resolved


def run_dev() -> int:
    """并行启动后端 (uvicorn) 与前端 (Nuxt), 任一退出则整体停止.

    与旧实现不同: 使用列表 argv + shell=False, 并在检测到非预期退出时
    把子进程退出码透传给 sys.exit, 使失败显式化.
    """
    backend_executable = _resolve_executable(_BACKEND_ARGV[0])
    frontend_executable = _resolve_executable(_FRONTEND_ARGV[0])
    backend_argv: tuple[str, ...] = (backend_executable, *_BACKEND_ARGV[1:])
    frontend_argv: tuple[str, ...] = (frontend_executable, *_FRONTEND_ARGV[1:])

    backend_cmd_str = " ".join(backend_argv)
    frontend_cmd_str = " ".join(frontend_argv)
    print("== Chathook 一键启动 ==")
    print(f"后端: {backend_cmd_str}")
    print(f"前端: cd {FRONTEND_DIR} && {frontend_cmd_str}")
    print("按 Ctrl+C 可同时关闭两个服务\n")

    # shell=False + argv 列表; 不使用环境变量继承 PATH 即可
    procs = [
        subprocess.Popen(
            backend_argv,
            cwd=ROOT,
            shell=False,
            text=True,
        ),
        subprocess.Popen(
            frontend_argv,
            cwd=FRONTEND_DIR,
            shell=False,
            text=True,
        ),
    ]

    first_exit_code = 0
    first_exited_label: str | None = None
    # 用户主动 Ctrl+C 时 (或 KeyboardInterrupt) 不视为失败,
    # 即使被 terminate() 杀掉的子进程返回非零退出码也忽略.
    interrupted_by_user = False

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
        interrupted_by_user = True
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

    if interrupted_by_user:
        # 用户主动中断 (Ctrl+C) → 视为正常退出, 忽略子进程退出码
        print("已全部关闭.")
        return 0
    if first_exit_code != 0:
        print(
            f"有进程异常退出 ({first_exited_label}, code={first_exit_code})"
        )
    else:
        print("已全部关闭.")
    return first_exit_code


if __name__ == "__main__":
    sys.exit(run_dev())
