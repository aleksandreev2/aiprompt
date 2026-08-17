from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlsplit

import httpx
from pydantic import ValidationError

from .schemas import ModelPlan


SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "novelai_prompt_plan",
        "strict": True,
        "schema": ModelPlan.model_json_schema(),
    },
}


@dataclass(frozen=True)
class LMStudioModelConfig:
    model_id: str
    context_length: int | None = None
    parallel: int | None = None
    flash_attention: bool | None = None
    offload_kv_cache_to_gpu: bool | None = None
    quantization: str | None = None


@dataclass(frozen=True)
class LMStudioStatus:
    reachable: bool
    models: list[str]
    message: str
    configs: dict[str, LMStudioModelConfig]


class LMStudioGenerationError(RuntimeError):
    pass


class LMStudioTruncatedOutput(LMStudioGenerationError):
    pass


class LMStudioInvalidJSON(LMStudioGenerationError):
    pass


class LMStudioInvalidPlan(LMStudioGenerationError):
    pass


class LMStudioClient:
    """LM Studio client. Construction performs zero network I/O."""

    def __init__(self) -> None:
        self.base_url = os.getenv("LMSTUDIO_BASE_URL", "http://127.0.0.1:1234/v1").rstrip("/")
        parsed = urlsplit(self.base_url)
        self.server_root = f"{parsed.scheme}://{parsed.netloc}"
        self._probe_timeout = httpx.Timeout(2.0, connect=0.75)
        self._generation_timeout = httpx.Timeout(120.0, connect=2.0)

    async def models(self) -> list[str]:
        """Return chat-capable model IDs from the OpenAI-compatible endpoint."""
        async with httpx.AsyncClient(timeout=self._probe_timeout) as client:
            response = await client.get(f"{self.base_url}/models")
            response.raise_for_status()
            data = response.json()
            models = [m.get("id", "") for m in data.get("data", []) if m.get("id")]
            chat_models = [m for m in models if "embedding" not in m.lower() and "embed" not in m.lower()]
            return chat_models or models

    async def model_configs(self) -> dict[str, LMStudioModelConfig]:
        """Read loaded-instance settings from LM Studio's native REST API.

        Failure is intentionally non-fatal; `/v1/models` remains the compatibility
        source of truth for model discovery.
        """
        async with httpx.AsyncClient(timeout=self._probe_timeout) as client:
            response = await client.get(f"{self.server_root}/api/v1/models")
            response.raise_for_status()
            data = response.json()

        result: dict[str, LMStudioModelConfig] = {}
        for model in data.get("models", []):
            if model.get("type") != "llm":
                continue
            key = str(model.get("key") or "").strip()
            if not key:
                continue
            loaded = model.get("loaded_instances") or []
            if not loaded:
                continue
            instance = loaded[0] or {}
            config = instance.get("config") or {}
            instance_id = str(instance.get("id") or key)
            quant = model.get("quantization") or {}
            cfg = LMStudioModelConfig(
                model_id=instance_id,
                context_length=config.get("context_length"),
                parallel=config.get("parallel"),
                flash_attention=config.get("flash_attention"),
                offload_kv_cache_to_gpu=config.get("offload_kv_cache_to_gpu"),
                quantization=quant.get("name"),
            )
            result[instance_id] = cfg
            result[key] = cfg
        return result

    async def status(self) -> LMStudioStatus:
        try:
            models = await self.models()
        except (httpx.HTTPError, OSError, ValueError) as exc:
            return LMStudioStatus(False, [], f"сервер не запущен ({type(exc).__name__})", {})

        if not models:
            return LMStudioStatus(True, [], "сервер запущен, но chat-модель не загружена", {})

        try:
            configs = await self.model_configs()
        except (httpx.HTTPError, OSError, ValueError):
            configs = {}

        return LMStudioStatus(True, models, f"подключено · chat-моделей: {len(models)}", configs)

    @staticmethod
    def _decode_content(content: Any) -> dict[str, Any]:
        if isinstance(content, dict):
            return content
        if not isinstance(content, str):
            raise LMStudioInvalidJSON(f"Unexpected assistant content type: {type(content).__name__}")

        text = content.strip()
        if text.startswith("```"):
            lines = text.splitlines()
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines).strip()

        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as exc:
            raise LMStudioInvalidJSON(
                f"LM Studio returned incomplete/invalid structured JSON at char {exc.pos}."
            ) from exc
        if not isinstance(parsed, dict):
            raise LMStudioInvalidJSON("Structured output root was not a JSON object.")
        return parsed

    async def plan(
        self,
        *,
        model: str,
        system: str,
        user: str,
        temperature: float = 0.30,
        max_tokens: int = 512,
    ) -> ModelPlan:
        # Explicit request-level sampling keeps the app deterministic regardless
        # of the values shown in LM Studio's chat UI preset.
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "response_format": SCHEMA,
            "temperature": temperature,
            "top_p": 0.8,
            "top_k": 20,
            "repeat_penalty": 1.05,
            "max_tokens": max_tokens,
            "stream": False,
        }

        async with httpx.AsyncClient(timeout=self._generation_timeout) as client:
            response = await client.post(f"{self.base_url}/chat/completions", json=payload)
            response.raise_for_status()
            try:
                body = response.json()
            except ValueError as exc:
                raise LMStudioInvalidJSON("LM Studio HTTP response itself was not JSON.") from exc

        try:
            choice = body["choices"][0]
        except (KeyError, IndexError, TypeError) as exc:
            raise LMStudioInvalidJSON("LM Studio response did not contain choices[0].") from exc

        finish_reason = choice.get("finish_reason")
        content = choice.get("message", {}).get("content", "")
        if finish_reason == "length":
            raise LMStudioTruncatedOutput(
                f"LM Studio hit max_tokens={max_tokens} before structured JSON completed."
            )

        parsed = self._decode_content(content)
        try:
            return ModelPlan.model_validate(parsed)
        except ValidationError as exc:
            raise LMStudioInvalidPlan("Structured JSON did not satisfy the compact prompt schema.") from exc
