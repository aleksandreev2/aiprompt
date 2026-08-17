# Offline-first startup

The Gradio application does not require LM Studio to be running at process startup.

Expected behavior:

1. `START.bat` / `python app.py` starts Gradio without contacting LM Studio during construction.
2. The page renders with an offline/awaiting-server status.
3. A 30-second UI timer probes LM Studio only after the browser UI exists; manual refresh is also available.
4. Starting LM Studio later populates the model selector automatically.
5. Stopping LM Studio later does not stop Gradio.
6. Pressing Generate while LM Studio is unavailable returns an in-page status message rather than raising an application-breaking exception.

Regression coverage lives in `tests/test_offline_startup.py` and `tests/test_real_startup.py`.
