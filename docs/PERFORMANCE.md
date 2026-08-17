# Performance profile — RTX 3060 Ti 8 GB

The application is intentionally optimized for short single-request inference.

## Recommended LM Studio load settings

For Huihui Qwen3 8B Abliterated v2 Q4_K_M on an RTX 3060 Ti 8 GB:

- Context Length: **4096** for normal prompt-compilation work.
- Max Concurrent Predictions: **1**.
- Flash Attention: **ON**.
- GPU Offload: **Max** if it fits without memory pressure.
- KV cache GPU offload: **ON** when it fits.
- Do not enable speculative decoding for this app unless you have deliberately configured a compatible draft model.

Increase context to 8192 only for unusually long multi-character descriptions. A larger context consumes more memory even when the actual request is small.

## Request-level limits used by this project

The application sends inference settings in each `/v1/chat/completions` request, so LM Studio's chat-panel sampling preset does not control these API calls:

- `/no_think`
- temperature: `0.30`
- top_p: `0.8`
- top_k: `20`
- repeat_penalty: `1.05`
- max_tokens: `512` for ordinary requests, `700` only for long descriptions
- compact retry: `420` tokens
- structured JSON schema

The old prototype allowed 2200 completion tokens. If a small model started filling arrays instead of selecting a few controls, it could run until the hard token limit. That behavior is removed.

## Why Max Concurrent Predictions = 1

This application queues generation with concurrency 1 and normally has only one active prompt-compilation request. Four LM Studio prediction slots provide no useful throughput here while reserving resources for concurrency the app does not use.

## Temperature

A GPU temperature increase during inference is expected because local inference can use the GPU continuously. The important optimization here is to finish the request quickly instead of allowing unnecessary thousands of output tokens.
