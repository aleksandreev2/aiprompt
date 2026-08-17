import os
import socket
import time

import httpx

os.environ["LMSTUDIO_BASE_URL"] = "http://127.0.0.1:65534/v1"
os.environ["GRADIO_ANALYTICS_ENABLED"] = "False"

from backend.app.gradio_ui import build_demo


def _free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def test_actual_gradio_http_boots_with_lmstudio_offline():
    port = _free_port()
    demo = build_demo()
    try:
        demo.queue(default_concurrency_limit=1).launch(
            server_name="127.0.0.1",
            server_port=port,
            inbrowser=False,
            prevent_thread_lock=True,
            show_error=True,
            quiet=True,
        )
        deadline = time.time() + 10
        last = None
        while time.time() < deadline:
            try:
                r = httpx.get(f"http://127.0.0.1:{port}/", timeout=1)
                if r.status_code == 200:
                    return
                last = f"HTTP {r.status_code}"
            except Exception as exc:
                last = repr(exc)
            time.sleep(0.25)
        raise AssertionError(f"UI did not become ready: {last}")
    finally:
        demo.close()
