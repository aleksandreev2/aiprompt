from __future__ import annotations

import hashlib
import logging
import os
import platform
import socket
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LOG_DIR = ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "startup.log"

os.environ.setdefault("GRADIO_ANALYTICS_ENABLED", "False")
os.environ.setdefault("GRADIO_TELEMETRY_ENABLED", "False")


def make_logger() -> logging.Logger:
    logger = logging.getLogger("novelai_prompt_lab")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")

    fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(formatter)
    logger.addHandler(sh)
    return logger


log = make_logger()


def missing_project_assets(root: Path) -> list[str]:
    """Return missing startup-critical assets.

    The knowledge base used to be one ``knowledge/verified_tags.csv`` file.
    Current repositories store the verified core as CSV shards under
    ``knowledge/tags/``. Keep the legacy file as a supported fallback so older
    working copies do not break, but never require it when shards exist.
    """
    missing: list[str] = []

    legacy_tags = root / "knowledge" / "verified_tags.csv"
    tag_dir = root / "knowledge" / "tags"
    has_tag_shards = tag_dir.is_dir() and any(tag_dir.glob("*.csv"))
    if not legacy_tags.is_file() and not has_tag_shards:
        missing.append(f"{tag_dir}{os.sep}*.csv (or legacy {legacy_tags})")

    required_files = [
        root / "knowledge" / "source" / "model_profile_v45.md",
        root / "backend" / "app" / "gradio_ui.py",
    ]
    missing.extend(str(p) for p in required_files if not p.is_file())
    return missing


def _ui_revision(root: Path) -> str:
    """Fingerprint files that define the browser/backend event contract."""
    digest = hashlib.sha256()
    for relative in (
        Path("backend/app/gradio_ui.py"),
        Path("backend/app/schemas.py"),
    ):
        path = root / relative
        if path.is_file():
            digest.update(relative.as_posix().encode("utf-8"))
            digest.update(path.read_bytes())
    return digest.hexdigest()[:10]


def _port_is_available(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((host, port))
        except OSError:
            return False
        return True


def choose_ui_port(root: Path = ROOT, host: str = "127.0.0.1") -> tuple[int, str]:
    """Choose a port tied to the current UI revision.

    A browser tab can stay open while the Python backend is updated. Gradio then
    sends the old event payload to the new callback signature and raises errors
    such as ``needed: 6, got: 5`` before our handler even runs. Giving each UI
    revision a different localhost origin prevents an old tab from silently
    attaching to a new event graph.
    """
    revision = _ui_revision(root)
    preferred = 7860 + (int(revision[:8], 16) % 900)
    if _port_is_available(host, preferred):
        return preferred, revision

    # Same revision may already be running. Fall back to an OS-selected free
    # port so a second launch still succeeds and opens a genuinely fresh page.
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((host, 0))
        return int(sock.getsockname()[1]), revision


def main() -> int:
    log.info("NovelAI Prompt Lab launcher starting")
    log.info("Python: %s", sys.version.replace("\n", " "))
    log.info("Platform: %s", platform.platform())
    log.info("Project root: %s", ROOT)
    log.info("LM Studio is NOT required for startup")

    missing = missing_project_assets(ROOT)
    if missing:
        raise RuntimeError("Missing required project files: " + ", ".join(missing))

    import gradio as gr
    import httpx
    import pydantic
    from backend.app.gradio_ui import CSS, THEME, demo, kb

    port, revision = choose_ui_port(ROOT)

    log.info("Gradio: %s", gr.__version__)
    log.info("httpx: %s", httpx.__version__)
    log.info("pydantic: %s", pydantic.__version__)
    log.info("Knowledge base: %d verified records", len(kb.tags))
    log.info("UI revision: %s", revision)
    log.info("Starting UI on fresh revision port: http://127.0.0.1:%d", port)

    demo.queue(default_concurrency_limit=1).launch(
        server_name="127.0.0.1",
        server_port=port,
        inbrowser=True,
        show_error=True,
        theme=THEME,
        css=CSS,
        quiet=False,
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        log.info("Stopped by user")
        raise SystemExit(0)
    except SystemExit:
        raise
    except BaseException as exc:
        log.error("FATAL STARTUP ERROR: %s: %s", type(exc).__name__, exc)
        log.error(traceback.format_exc())
        print("\n" + "=" * 72)
        print("STARTUP FAILED. The window will stay open.")
        print(f"Log: {LOG_FILE}")
        print("=" * 72)
        try:
            input("Press Enter to close...")
        except EOFError:
            pass
        raise SystemExit(1)
