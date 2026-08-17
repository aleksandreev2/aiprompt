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


def main() -> int:
    log.info("NovelAI Prompt Lab launcher starting")
    log.info("Python: %s", sys.version.replace("\n", " "))
    log.info("Platform: %s", platform.platform())
    log.info("Project root: %s", ROOT)
    log.info("LM Studio is NOT required for startup")

    required = [
        ROOT / "knowledge" / "verified_tags.csv",
        ROOT / "knowledge" / "source" / "model_profile_v45.md",
        ROOT / "backend" / "app" / "gradio_ui.py",
    ]
    missing = [str(p) for p in required if not p.exists()]
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
