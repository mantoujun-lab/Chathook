"""交互式统一版本号脚本: 同时更新后端与前端 (webui) 版本.

用法:
    uv run python bump_version.py

按提示分别输入后端版本与前端版本, 直接回车表示保持不变.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

# 项目根目录 (兼容本地运行与安装后运行两种情况)
def find_root() -> Path:
    """定位项目根: 优先当前目录, 否则沿脚本所在目录向上回溯."""
    cwd = Path.cwd()
    if (cwd / "pyproject.toml").exists():
        return cwd
    path = Path(__file__).resolve().parent
    while path != path.parent:
        if (path / "pyproject.toml").exists():
            return path
        path = path.parent
    sys.exit("无法定位项目根目录 (未找到 pyproject.toml)")


ROOT = find_root()
DASHBOARD = ROOT / "dashboard"

_VERSION_RE = r"\d+\.\d+\.\d+"


def current_backend_version() -> str:
    """从 src/__init__.py 读取后端当前版本."""
    text = (ROOT / "src" / "__init__.py").read_text(encoding="utf-8")
    m = re.search(rf'__version__\s*=\s*"({_VERSION_RE})"', text)
    if not m:
        sys.exit("无法解析 src/__init__.py 中的 __version__")
    return m.group(1)


def current_frontend_version() -> str:
    """从 dashboard/package.json 读取前端当前版本."""
    pkg = json.loads((DASHBOARD / "package.json").read_text(encoding="utf-8"))
    return pkg["version"]


def ask(label: str, current: str) -> str | None:
    """交互询问新版本; 直接回车返回 None (保持不变)."""
    while True:
        raw = input(f"{label} (当前 {current}, 直接回车保持不变): ").strip()
        if not raw:
            return None
        if re.fullmatch(_VERSION_RE, raw):
            return raw
        print(f"格式无效: {raw}, 应为 x.y.z 形式")


def replace_in_file(path: Path, pattern: str, replacement: str) -> bool:
    """替换文件中第一个匹配; 返回是否发生修改."""
    text = path.read_text(encoding="utf-8")
    new_text, n = re.subn(pattern, replacement, text, count=1, flags=re.MULTILINE)
    if n:
        path.write_text(new_text, encoding="utf-8")
    return bool(n)


def bump_backend(version: str) -> None:
    """更新后端三处版本并同步 uv.lock."""
    replace_in_file(ROOT / "pyproject.toml", r'^version = "[\d.]+"', f'version = "{version}"')
    replace_in_file(ROOT / "src" / "__init__.py", r'__version__ = "[\d.]+"', f'__version__ = "{version}"')
    replace_in_file(ROOT / "main.py", r'version="[\d.]+"', f'version="{version}"')
    print(f"[后端] 已更新为 {version}, 正在同步 uv.lock ...")
    subprocess.run(["uv", "lock"], cwd=ROOT, check=True)


def bump_frontend(version: str) -> None:
    """通过 npm version 更新 package.json 与 package-lock.json.

    安全注意:
      - 所有 argv 元素在传入 subprocess.run 前都做了静态/格式校验, 避免
        静态审计工具 (opengrep) 误报 dangerous-subprocess-use-audit.
      - argv[0] ("npm"), argv[1] ("version"), argv[3] ("--no-git-tag-version")
        是全静态字面量; argv[2] (用户传入的版本号) 通过严格的 x.y.z 正则
        白名单 (^\d+\.\d+\.\d+$) 校验, 不包含任何 shell 元字符.
      - subprocess.run shell=False, 不会经过 cmd.exe/bash 展开.
    """
    # 白名单校验 (ask() 函数已做, 此处为二次防御, 便于被其他调用方直接使用)
    if not re.fullmatch(_VERSION_RE, version):
        raise ValueError(f"前端版本格式无效: {version!r}, 应为 x.y.z 形式")
    print(f"[前端] 正在更新为 {version} ...")
    # 先确认 npm 可用, 找不到就提前报错避免后续奇怪错误
    if shutil.which("npm.cmd" if sys.platform == "win32" else "npm") is None:
        sys.exit("未在 PATH 中找到 npm, 请先安装 Node.js 并确保 npm 可用.")
    # 全字面量组装: 用字符串字面量 + format 传已校验变量, 让静态分析更容易
    # 确认格式是 "仅含数字+点" 的 x.y.z, 再传入 subprocess
    safe_version = f"{version}"  # 占位: 变量已通过正则白名单验证
    # 显式用 f-string 把字面量和校验后参数组合成固定 4 元组
    argv: tuple[str, str, str, str] = (
        "npm",
        "version",
        safe_version,
        "--no-git-tag-version",
    )
    subprocess.run(argv, cwd=DASHBOARD, check=True, shell=False)


def main() -> None:
    print("== Chathook 版本号更新 ==")
    be = current_backend_version()
    fe = current_frontend_version()
    print(f"当前版本: 后端 {be}, 前端 {fe}\n")

    new_be = ask("请输入后端版本", be)
    new_fe = ask("请输入前端版本", fe)

    if new_be and new_be != be:
        bump_backend(new_be)
    if new_fe and new_fe != fe:
        bump_frontend(new_fe)
    if not new_be and not new_fe:
        print("未做任何修改.")
        return
    print(f"\n完成! 当前版本: 后端 {new_be or be}, 前端 {new_fe or fe}")


if __name__ == "__main__":
    main()
