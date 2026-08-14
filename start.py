"""
Chathook 一键启动脚本：同时启动后端 (FastAPI) 与前端 (Nuxt)。

用法(任意平台，需已安装 uv 与 Node.js)
    uv run python start.py

按 Ctrl+C 即可同时关闭两个服务。
"""

from __future__ import annotations

import os
import subprocess
import sys
import time

# 项目根目录（即脚本所在目录）
ROOT = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(ROOT, "dashboard")

BACKEND_CMD = "uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000"
FRONTEND_CMD = "npm run dev"


def main() -> int:
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
                    print("有进程已退出，停止全部服务...")
                    raise KeyboardInterrupt
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\n正在关闭服务...")
    finally:
        for proc in procs:
            if proc.poll() is None:
                proc.terminate()
        # 等待优雅退出，超时则强制结束
        for proc in procs:
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()

    print("已全部关闭。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
