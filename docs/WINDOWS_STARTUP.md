# Windows startup

Use `START.bat` from the project root.

The UI starts independently of LM Studio. LM Studio may be closed, have no model loaded, or be started later.

Startup behavior:
- discovers `py -3` first, then `python`;
- creates `.venv` only when missing;
- uses pinned/tested dependencies from `requirements.lock.txt`;
- does not depend on activating a virtualenv;
- logs Python/Gradio/import/startup failures to `logs/startup.log`;
- keeps the console open on failure;
- lets Gradio choose another local port if 7860 is busy.

If startup still fails, run `START_DEBUG.bat` and attach `logs/startup.log` plus the diagnostic output.
