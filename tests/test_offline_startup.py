import asyncio
import os

os.environ["LMSTUDIO_BASE_URL"] = "http://127.0.0.1:65534/v1"

from backend.app.lmstudio import LMStudioClient
from backend.app.gradio_ui import generate_prompt


def test_lmstudio_client_is_safe_when_server_is_down():
    client = LMStudioClient()
    status = asyncio.run(client.status())
    assert status.reachable is False
    assert status.models == []


def test_generate_while_offline_returns_ui_message_instead_of_exception():
    result = asyncio.run(
        generate_prompt(
            "portrait, black hair, from below",
            None,
            "Balanced — теги + prose",
            True,
            8,
        )
    )
    assert len(result) == 13
    assert "LM Studio" in result[-1]
    assert "интерфейс" in result[-1].lower()
