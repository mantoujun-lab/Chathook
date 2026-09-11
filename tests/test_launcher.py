"""启动器辅助逻辑测试: 前端产物新鲜度判断与静态/兜底路由."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import main


def _touch(path: Path, mtime: float) -> None:
    """写入占位文件并把 mtime 固定为给定值, 便于稳定比较."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("x", encoding="utf-8")
    os.utime(path, (mtime, mtime))


@pytest.fixture()
def frontend(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """把启动器的前端路径重定向到临时目录, 避免触碰真实产物."""
    frontend_dir = tmp_path / "dashboard"
    output_dir = frontend_dir / ".output" / "public"
    monkeypatch.setattr(main, "FRONTEND_DIR", frontend_dir)
    monkeypatch.setattr(main, "OUTPUT_DIR", output_dir)
    monkeypatch.setattr(main, "INDEX_FILE", output_dir / "index.html")
    monkeypatch.setattr(
        main, "_INSTALL_MARKER", frontend_dir / "node_modules" / ".package-lock.json"
    )
    return frontend_dir


def test_needs_rebuild_when_index_missing(frontend: Path) -> None:
    assert main._needs_rebuild() is True


def test_needs_rebuild_when_output_newer(frontend: Path) -> None:
    _touch(frontend / "package.json", 100)
    _touch(frontend / "package-lock.json", 100)
    _touch(frontend / "nuxt.config.ts", 100)
    _touch(frontend / "app" / "pages" / "index.vue", 100)
    _touch(frontend / ".output" / "public" / "index.html", 200)

    assert main._needs_rebuild() is False


def test_needs_rebuild_when_source_newer(frontend: Path) -> None:
    _touch(frontend / "package.json", 100)
    _touch(frontend / ".output" / "public" / "index.html", 200)
    _touch(frontend / "app" / "pages" / "index.vue", 300)

    assert main._needs_rebuild() is True


def test_needs_install_when_marker_missing(frontend: Path) -> None:
    _touch(frontend / "package.json", 100)

    assert main._needs_install() is True


def test_needs_install_when_deps_newer(frontend: Path) -> None:
    _touch(frontend / "node_modules" / ".package-lock.json", 100)
    _touch(frontend / "package.json", 200)

    assert main._needs_install() is True


def test_needs_install_when_marker_current(frontend: Path) -> None:
    _touch(frontend / "package.json", 100)
    _touch(frontend / "package-lock.json", 100)
    _touch(frontend / "node_modules" / ".package-lock.json", 200)

    assert main._needs_install() is False


def test_resolve_spa_file_falls_back_on_traversal(frontend: Path) -> None:
    _touch(frontend / ".output" / "public" / "index.html", 100)

    assert main._resolve_spa_file("../outside.txt") == main.INDEX_FILE


def test_resolve_spa_file_returns_existing_file(frontend: Path) -> None:
    _touch(frontend / ".output" / "public" / "index.html", 100)
    _touch(frontend / ".output" / "public" / "logo.svg", 100)

    expected = (frontend / ".output" / "public" / "logo.svg").resolve()
    assert main._resolve_spa_file("logo.svg") == expected


def test_spa_fallback_rejects_unknown_api_path() -> None:
    client = TestClient(main.app)

    assert client.get("/api/does-not-exist").status_code == 404


def test_spa_fallback_404_without_output(frontend: Path) -> None:
    client = TestClient(main.app)

    assert client.get("/some/spa/route").status_code == 404


def test_spa_fallback_serves_index_for_frontend_route(frontend: Path) -> None:
    _touch(frontend / ".output" / "public" / "index.html", 100)
    client = TestClient(main.app)

    resp = client.get("/some/spa/route")

    assert resp.status_code == 200
    assert resp.text == "x"
