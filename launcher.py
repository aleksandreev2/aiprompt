from __future__ import annotations

import logging
import os
import platform
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

    log.info("Gradio: %s", gr.__version__)
    log.info("httpx: %s", httpx.__version__)
    log.info("pydantic: %s", pydantic.__version__)
    log.info("Knowledge base: %d verified records", len(kb.tags))
    log.info("Starting UI. Gradio will choose the first free port from 7860 upward.")

    demo.queue(default_concurrency_limit=1).launch(
        server_name="127.0.0.1",
        server_port=None,
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
