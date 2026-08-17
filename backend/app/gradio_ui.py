from __future__ import annotations

import logging
import os
import traceback
from pathlib import Path

import gradio as gr
from dotenv import load_dotenv

from .compiler import compile_plan
from .knowledge import KnowledgeBase
from .lmstudio import (
    LMStudioClient,
    LMStudioInvalidJSON,
    LMStudioInvalidPlan,
    LMStudioTruncatedOutput,
)
from .prompting import build_prompt_context

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

kb = KnowledgeBase(ROOT / os.getenv("NAI_KNOWLEDGE_DIR", "knowledge"))
lm = LMStudioClient()

LOG_DIR = ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True)
_runtime_log = logging.getLogger("novelai_prompt_lab.runtime")
if not _runtime_log.handlers:
    _runtime_log.setLevel(logging.INFO)
    _fh = logging.FileHandler(LOG_DIR / "runtime.log", encoding="utf-8")
    _fh.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
    _runtime_log.addHandler(_fh)

MODE_LABEL_TO_VALUE = {
    "Balanced — теги + prose": "balanced",
    "Tag-heavy — максимум тегов": "strict_tags",
    "Prose Fallback — больше естественного языка": "prose_fallback",
}

DETAIL_LABEL_TO_VALUE = {
    "Literal — только сказанное": "literal",
    "Enhanced — аккуратно дополнить": "enhanced",
    "Rich — полноценный production prompt": "rich",
}

THEME = gr.themes.Soft(
    primary_hue="indigo",
    neutral_hue="slate",
    radius_size="md",
    text_size="md",
)

CSS = """
.gradio-container { max-width: 1500px !important; }
#app-title h1 { margin-bottom: 0.15rem; }
#app-title p { opacity: 0.78; margin-top: 0; }
#intent-box textarea { font-size: 16px; line-height: 1.5; }
.output-box textarea { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace !important; }
.section-note { opacity: 0.72; font-size: 0.92rem; }
"""


def _status_markdown(state: str, message: str, detail: str = "") -> str:
    icon = {"ok": "🟢", "warn": "🟡", "offline": "⚪"}.get(state, "⚪")
    suffix = f"  ·  {detail}" if detail else ""
    return (
        f"{icon} **LM Studio:** {message}  ·  **Verified:** {len(kb.tags)}"
        f"  ·  **Retrieval concepts:** {len(kb.concepts)}{suffix}"
    )


def _boot_status() -> str:
    return _status_markdown("offline", "интерфейс запущен · ожидаем локальный сервер")


async def refresh_models(current_model: str | None = None):
    status = await lm.status()
    current_model = (current_model or "").strip()

    if not status.reachable:
        choices = [current_model] if current_model else []
        return (
            gr.update(choices=choices, value=current_model or None),
            _status_markdown("offline", "сервер не запущен — UI работает автономно"),
        )

    if not status.models:
        return (
            gr.update(choices=[current_model] if current_model else [], value=current_model or None),
            _status_markdown("warn", "сервер запущен, но chat-модель не загружена"),
        )

    preferred = os.getenv("LMSTUDIO_MODEL", "").strip()
    if current_model in status.models:
        value = current_model
    elif preferred in status.models:
        value = preferred
    else:
        value = status.models[0]

    cfg = status.configs.get(value)
    detail = ""
    state = "ok"
    if cfg:
        pieces = []
        if cfg.quantization:
            pieces.append(cfg.quantization)
        if cfg.context_length:
            pieces.append(f"ctx {cfg.context_length}")
        if cfg.parallel is not None:
            pieces.append(f"parallel {cfg.parallel}")
            if cfg.parallel > 1:
                state = "warn"
                pieces.append("для этого приложения лучше 1")
        if cfg.flash_attention is not None:
            pieces.append("FlashAttn ON" if cfg.flash_attention else "FlashAttn OFF")
        detail = " · ".join(pieces)

    return (
        gr.update(choices=status.models, value=value),
        _status_markdown(state, status.message, detail),
    )


def _character_updates(characters):
    updates = []
    for idx in range(6):
        if idx < len(characters) and characters[idx].prompt.strip():
            char = characters[idx]
            label = char.label.strip() or f"Character {idx + 1}"
            updates.append(gr.update(value=char.prompt, label=label, visible=True))
        else:
            updates.append(gr.update(value="", label=f"Character {idx + 1}", visible=False))
    return updates


def _empty_character_updates():
    return [gr.update(value="", visible=False, label=f"Character {i + 1}") for i in range(6)]


def _offline_generation_result(message: str):
    return (
        "",
        "",
        *_empty_character_updates(),
        "",
        "",
        "",
        "",
        f"⚪ {message}",
    )


async def generate_prompt(
    intent: str,
    model: str | None,
    mode_label: str,
    detail_label: str,
    add_quality_tags: bool,
    max_context_tags: int,
):
    intent = (intent or "").strip()
    if not intent:
        return _offline_generation_result("Сначала опиши сцену или нужные изменения.")

    selected_model = (model or "").strip()
    if not selected_model:
        status = await lm.status()
        if not status.reachable:
            return _offline_generation_result(
                "LM Studio пока выключен. Интерфейс остаётся запущенным — открой LM Studio, "
                "запусти Local Server, и модель подхватится автоматически."
            )
        if not status.models:
            return _offline_generation_result(
                "LM Studio подключён, но chat-модель не загружена. Загрузи GGUF — перезапускать интерфейс не нужно."
            )
        selected_model = status.models[0]

    mode = MODE_LABEL_TO_VALUE.get(mode_label, "balanced")
    detail_level = DETAIL_LABEL_TO_VALUE.get(detail_label, "rich")
    context_limit = max(0, min(int(max_context_tags), 16))
    system, retrieval = build_prompt_context(
        kb,
        intent,
        context_limit,
        mode,
        bool(add_quality_tags),
        detail_level,
    )

    user = (
        "Create ONE coherent NovelAI prompt plan for the visual intent below. "
        "The RETRIEVAL PACK already contains hard requirements and locks. "
        "Do not translate the sentence literally; decompose it into useful prompt controls. "
        "Do not create alternatives or contradictory options.\n\nUSER INTENT:\n" + intent
    )

    base_budget = {
        "literal": 280,
        "enhanced": 360,
        "rich": 460,
    }[detail_level]
    first_budget = min(600, base_budget + (80 if len(intent) >= 1200 else 0))

    try:
        plan = await lm.plan(
            model=selected_model,
            system=system,
            user=user,
            temperature=0.42 if detail_level == "rich" else 0.32,
            max_tokens=first_budget,
        )
    except (LMStudioTruncatedOutput, LMStudioInvalidJSON, LMStudioInvalidPlan) as first_exc:
        _runtime_log.warning(
            "First structured generation failed: %s: %s",
            type(first_exc).__name__,
            first_exc,
        )
        retry_system, retrieval = build_prompt_context(
            kb,
            intent,
            min(context_limit, 4),
            mode,
            bool(add_quality_tags),
            "enhanced",
        )
        retry_user = (
            "COMPACT RETRY. Return only valid JSON for one coherent prompt. "
            "Preserve every REQUIRED USER CONCEPT and LOCK. Remove redundancy.\n\n"
            "USER INTENT:\n" + intent
        )
        try:
            plan = await lm.plan(
                model=selected_model,
                system=retry_system,
                user=retry_user,
                temperature=0.24,
                max_tokens=340,
            )
        except (LMStudioTruncatedOutput, LMStudioInvalidJSON, LMStudioInvalidPlan) as exc:
            _runtime_log.error(
                "Compact structured retry failed: %s: %s",
                type(exc).__name__,
                exc,
            )
            return _offline_generation_result(
                "LM Studio отвечает, но structured output дважды получился неполным. "
                "Приложение не упало. Попробуй Enhanced depth или Context Length 4096–8192. "
                f"Диагностика: {type(exc).__name__}. Подробности: logs/runtime.log"
            )
        except Exception as exc:
            _runtime_log.error("Compact retry request failed: %s\n%s", exc, traceback.format_exc())
            return _offline_generation_result(
                f"LM Studio доступен, но повторный запрос завершился ошибкой {type(exc).__name__}. "
                "Подробности: logs/runtime.log"
            )
    except Exception as exc:
        _runtime_log.error("LM Studio request failed: %s\n%s", exc, traceback.format_exc())
        return _offline_generation_result(
            f"Не удалось выполнить запрос к LM Studio ({type(exc).__name__}). UI продолжает работать. "
            "Подробности: logs/runtime.log"
        )

    result = compile_plan(
        plan,
        kb,
        selected_model,
        intent=intent,
        retrieval=retrieval,
        mode=mode,
    )

    validation_lines = []
    if result.warnings:
        validation_lines.extend(f"- {x}" for x in result.warnings)
    else:
        validation_lines.append("- Нет предупреждений.")
    if result.coverage:
        validation_lines.append("\n**Coverage**")
        validation_lines.extend(f"- {x}" for x in result.coverage)
    if result.conflicts_removed:
        validation_lines.append("\n**Removed / normalized**")
        validation_lines.extend(f"- {x}" for x in result.conflicts_removed)
    warnings = "\n".join(validation_lines)

    notes = "\n".join(f"- {x}" for x in result.notes) or "Нет дополнительных заметок."
    verified = ", ".join(result.verified_tags_used) or "—"

    diagnostic_sections = []
    if result.observed_candidates:
        diagnostic_sections.append(
            "**Observed/community candidates**\n"
            + "\n".join(f"- {x}" for x in result.observed_candidates)
        )
    if result.unverified_candidates:
        diagnostic_sections.append(
            "**Unverified candidates**\n"
            + "\n".join(f"- {x}" for x in result.unverified_candidates)
        )
    if result.prose_fallbacks:
        diagnostic_sections.append(
            "**Precise prose fallbacks**\n"
            + "\n".join(f"- {x}" for x in result.prose_fallbacks)
        )
    diagnostics = "\n\n".join(diagnostic_sections) or "—"

    return (
        result.base_prompt,
        result.undesired_content,
        *_character_updates(result.characters),
        warnings,
        notes,
        verified,
        diagnostics,
        (
            f"🟢 Готово · model: `{result.model}` · verified: **{len(result.verified_tags_used)}** "
            f"· observed: **{len(result.observed_candidates)}** "
            f"· unknown/prose: **{len(result.unverified_candidates) + len(result.prose_fallbacks)}** "
            f"· required: **{len(retrieval.required)}**"
        ),
    )


def clear_outputs():
    return (
        "",
        "",
        *_empty_character_updates(),
        "",
        "",
        "",
        "",
        "",
    )


def build_demo() -> gr.Blocks:
    with gr.Blocks(title="NovelAI Prompt Lab", fill_width=True) as demo:
        gr.Markdown(
            "# NovelAI Prompt Lab\n"
            "Русский/английский intent → hybrid retrieval → LM Studio → deterministic compiler → NovelAI prompt.",
            elem_id="app-title",
        )

        with gr.Row(equal_height=True):
            connection_status = gr.Markdown(_boot_status())
            refresh_button = gr.Button("↻ Проверить LM Studio", size="sm", min_width=190)

        gr.Markdown(
            "UI стартует без LM Studio. Retrieval и локальная knowledge-base загружаются сразу; "
            "LLM нужен только после нажатия Generate.",
            elem_classes=["section-note"],
        )

        with gr.Row():
            with gr.Column(scale=7):
                intent = gr.Textbox(
                    label="Что хочешь получить",
                    placeholder=(
                        "Опиши сцену обычным языком. Явные детали становятся requirements; "
                        "неуказанные внешность/стиль/партнёр не должны выдумываться."
                    ),
                    lines=8,
                    max_lines=18,
                    autofocus=True,
                    elem_id="intent-box",
                )
                with gr.Row():
                    generate_button = gr.Button("Generate Prompt", variant="primary", scale=4)
                    clear_button = gr.Button("Очистить результат", scale=1)

            with gr.Column(scale=3):
                model = gr.Dropdown(
                    choices=[],
                    value=None,
                    label="LM Studio model",
                    info="Подхватится автоматически после запуска Local Server.",
                    allow_custom_value=True,
                )
                mode = gr.Radio(
                    choices=list(MODE_LABEL_TO_VALUE.keys()),
                    value="Tag-heavy — максимум тегов",
                    label="Prompt language",
                    info="Tag-heavy предпочитает compact prompt atoms; precise prose остаётся разрешённым fallback.",
                )
                detail_level = gr.Radio(
                    choices=list(DETAIL_LABEL_TO_VALUE.keys()),
                    value="Rich — полноценный production prompt",
                    label="Prompt depth",
                    info="Rich расширяет только полезные dimensions; locks не дают выдумывать пустые атрибуты.",
                )
                add_quality_tags = gr.Checkbox(
                    value=True,
                    label="Add Quality Tags включён в NovelAI",
                    info="Не дублировать автоматический quality preamble.",
                )
                max_context_tags = gr.Slider(
                    minimum=0,
                    maximum=16,
                    value=8,
                    step=2,
                    label="Retrieval context",
                    info="Сколько top concepts давать модели. Explicit requirements сохраняются независимо от лимита.",
                )

        generation_status = gr.Markdown("")

        gr.Markdown("## Готовый prompt")
        base_prompt = gr.Textbox(
            label="Base Prompt",
            lines=7,
            max_lines=18,
            interactive=True,
            buttons=["copy"],
            elem_classes=["output-box"],
        )
        undesired_content = gr.Textbox(
            label="Undesired Content / UC",
            lines=3,
            max_lines=10,
            interactive=True,
            buttons=["copy"],
            elem_classes=["output-box"],
        )

        with gr.Accordion("Character Prompts", open=True):
            gr.Markdown(
                "Появляются для многоперсонажных сцен; глобальная композиция остаётся в Base Prompt.",
                elem_classes=["section-note"],
            )
            character_boxes = []
            for idx in range(6):
                character_boxes.append(
                    gr.Textbox(
                        label=f"Character {idx + 1}",
                        lines=3,
                        max_lines=10,
                        interactive=True,
                        visible=False,
                        buttons=["copy"],
                        elem_classes=["output-box"],
                    )
                )

        with gr.Tabs():
            with gr.Tab("Validation / Coverage"):
                warnings = gr.Markdown("")
                verified_tags = gr.Textbox(
                    label="Locally verified controls used",
                    lines=4,
                    max_lines=10,
                    interactive=False,
                    buttons=["copy"],
                    elem_classes=["output-box"],
                )
            with gr.Tab("Observed / Unverified / Prose"):
                prose_fallbacks = gr.Markdown("")
            with gr.Tab("Model notes"):
                notes = gr.Markdown("")

        outputs = [
            base_prompt,
            undesired_content,
            *character_boxes,
            warnings,
            notes,
            verified_tags,
            prose_fallbacks,
            generation_status,
        ]
        inputs = [intent, model, mode, detail_level, add_quality_tags, max_context_tags]

        generate_button.click(fn=generate_prompt, inputs=inputs, outputs=outputs, show_progress="full")
        intent.submit(fn=generate_prompt, inputs=inputs, outputs=outputs, show_progress="full")
        clear_button.click(fn=clear_outputs, inputs=None, outputs=outputs, show_progress="hidden")
        refresh_button.click(
            fn=refresh_models,
            inputs=[model],
            outputs=[model, connection_status],
            show_progress="hidden",
        )

        reconnect_timer = gr.Timer(value=30.0, active=True)
        reconnect_timer.tick(
            fn=refresh_models,
            inputs=[model],
            outputs=[model, connection_status],
            show_progress="hidden",
        )

    return demo


demo = build_demo()
