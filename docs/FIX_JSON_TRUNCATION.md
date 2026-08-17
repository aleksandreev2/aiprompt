# Fix: LM Studio structured JSON truncation

Observed failure pattern from LM Studio:

- model context: 4096
- prompt: about 2638 tokens
- requested completion: 2200 tokens
- LM Studio performed context shifts
- completion stopped at the token budget with `finish_reason: length`
- assistant content ended in the middle of a JSON string
- the UI then surfaced a misleading `JSONDecodeError`

This build fixes the failure at multiple layers:

1. No generic tag padding. Only exact lexical tag matches are inserted as optional vocabulary.
2. Russian free-form input may inject zero vocabulary rows; the LLM proposes a small number of candidates and the full local database validates them afterward.
3. Structured schema has hard list-size caps.
4. First generation uses **512 max completion tokens** for ordinary requests; unusually long descriptions may use **700**.
5. Truncated/invalid structured output is detected explicitly before parsing.
6. One automatic retry is performed with zero vocabulary context, lower temperature, and a **420-token** completion budget.
7. UC/negative tags accidentally emitted in positive prompt sections are deterministically diverted to UC.
8. Runtime failures are logged to `logs/runtime.log`; they are no longer mislabeled as an offline LM Studio server.

Ordinary requests are designed to work with a 4096 model context. 8192 is optional for genuinely long or multi-character descriptions when memory permits.
