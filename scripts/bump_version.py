"""交互式统一版本号脚本: 同时更新后端与前端 (webui) 版本.

用法:
    uv run bump

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

# 后端版本号所在文件 (相对项目根); uv.lock 由 `uv lock` 重新生成
_BACKEND_FILES = ("pyproject.toml", "src/__init__.py", "main.py")


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
    """替换文件中第一个匹配; 返回是否发生修改.

    以 ``newline=""`` 读写, 保留文件原有行尾风格 (LF/CRLF), 避免脚本运行后
    仅因换行符差异而弄脏工作区.
    """
    with path.open(encoding="utf-8", newline="") as fh:
        text = fh.read()
    new_text, n = re.subn(pattern, replacement, text, count=1, flags=re.MULTILINE)
    if n:
        with path.open("w", encoding="utf-8", newline="") as fh:
            fh.write(new_text)
    return bool(n)


def resolve_executable(name: str) -> str:
    """解析可执行文件的绝对路径, 找不到时退出.

    Windows 上 ``subprocess`` 不会为无后缀的名字补全 ``.cmd``, 因此必须先用
    ``shutil.which`` 解析 (例如 ``npm`` -> ``npm.cmd``), 否则会抛
    ``FileNotFoundError``.
    """
    resolved = shutil.which(name)
    if resolved is None:
        sys.exit(f"未在 PATH 中找到 {name!r}, 请确认它已安装并可用.")
    return resolved


def _snapshot(paths: list[Path]) -> dict[Path, bytes]:
    """记录将被改动文件的原始字节, 供失败时无损回滚."""
    return {p: p.read_bytes() for p in paths if p.is_file()}


def _restore(snapshot: dict[Path, bytes]) -> None:
    """把文件恢复到快照内容, 避免留下只改了一半的版本号."""
    for path, original in snapshot.items():
        path.write_bytes(original)


def bump_backend(version: str, uv: str) -> None:
    """更新后端三处版本并同步 uv.lock (``uv`` 由调用方预先解析)."""
    replace_in_file(ROOT / "pyproject.toml", r'^version = "[\d.]+"', f'version = "{version}"')
    replace_in_file(ROOT / "src" / "__init__.py", r'__version__ = "[\d.]+"', f'__version__ = "{version}"')
    replace_in_file(ROOT / "main.py", r'version="[\d.]+"', f'version="{version}"')
    print(f"[后端] 已更新为 {version}, 正在同步 uv.lock ...")
    # uv 是 shutil.which 解析出的绝对路径, 参数为静态字面量; shell=False 不经过 shell.
    subprocess.run([uv, "lock"], cwd=ROOT, check=True, shell=False)  # nosemgrep: python.lang.security.audit.dangerous-subprocess-use-audit


def bump_frontend(version: str, npm: str) -> None:
    r"""通过 npm version 更新 package.json 与 package-lock.json.

    安全注意:
      - argv[0] 是经 shutil.which 解析出的绝对路径 (Windows 上为 npm.cmd);
        argv[1] ("version") 与 argv[3] ("--no-git-tag-version") 是全静态字面量;
        argv[2] (版本号) 通过严格的 x.y.z 正则白名单 (^\d+\.\d+\.\d+$) 校验,
        不包含任何 shell 元字符.
      - subprocess.run shell=False, 不会经过 cmd.exe/bash 展开.
    """
    # 白名单校验 (ask() 函数已做, 此处为二次防御, 便于被其他调用方直接使用)
    if not re.fullmatch(_VERSION_RE, version):
        raise ValueError(f"前端版本格式无效: {version!r}, 应为 x.y.z 形式")
    print(f"[前端] 正在更新为 {version} ...")
    argv: tuple[str, str, str, str] = (
        npm,
        "version",
        version,
        "--no-git-tag-version",
    )
    subprocess.run(argv, cwd=DASHBOARD, check=True, shell=False)  # nosemgrep: python.lang.security.audit.dangerous-subprocess-use-audit


def main() -> None:
    print("== Chathook 版本号更新 ==")
    be = current_backend_version()
    fe = current_frontend_version()
    print(f"当前版本: 后端 {be}, 前端 {fe}\n")

    new_be = ask("请输入后端版本", be)
    new_fe = ask("请输入前端版本", fe)

    if not new_be and not new_fe:
        print("未做任何修改.")
        return

    do_backend = bool(new_be) and new_be != be
    do_frontend = bool(new_fe) and new_fe != fe

    # 先解析所需可执行文件: 任一缺失时在修改任何文件之前退出, 避免只改了半个版本号
    uv = resolve_executable("uv") if do_backend else None
    npm = (
        resolve_executable("npm.cmd" if sys.platform == "win32" else "npm")
        if do_frontend
        else None
    )

    # 事务化: 记录所有将被改动的文件, 任一步骤失败时整体回滚
    tracked: list[Path] = []
    if do_backend:
        tracked += [ROOT / name for name in _BACKEND_FILES]
        tracked.append(ROOT / "uv.lock")
    if do_frontend:
        tracked += [DASHBOARD / "package.json", DASHBOARD / "package-lock.json"]
    snapshot = _snapshot(tracked)

    try:
        if do_backend and new_be is not None and uv is not None:
            bump_backend(new_be, uv)
        if do_frontend and new_fe is not None and npm is not None:
            bump_frontend(new_fe, npm)
    except Exception as exc:  # 统一回滚后退出, 不留下部分更新
        _restore(snapshot)
        sys.exit(f"版本更新失败, 已回滚对文件的改动: {exc}")

    print(f"\n完成! 当前版本: 后端 {new_be or be}, 前端 {new_fe or fe}")


if __name__ == "__main__":
    main()
