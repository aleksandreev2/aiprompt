from __future__ import annotations

import os
import platform
import socket
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)

print("NovelAI Prompt Lab diagnostics")
print("=" * 60)
print("Python:", sys.version)
print("Executable:", sys.executable)
print("Platform:", platform.platform())
print("Root:", ROOT)
print("LM Studio required for boot: NO")

for port in range(7860, 7866):
    s = socket.socket()
    try:
        s.bind(("127.0.0.1", port))
        state = "free"
    except OSError:
        state = "busy"
    finally:
        s.close()
    print(f"Port {port}: {state}")

print("\nDependencies:")
for name in ["gradio", "httpx", "pydantic", "dotenv"]:
    try:
        mod = __import__(name)
        print(f"  {name}: OK {getattr(mod, '__version__', '')}")
    except Exception as e:
        print(f"  {name}: FAIL {type(e).__name__}: {e}")

print("\nProject import:")
try:
    from backend.app.gradio_ui import demo, kb
    print("  UI import: OK")
    print(f"  Verified records: {len(kb.tags)}")
except Exception as e:
    print(f"  UI import: FAIL {type(e).__name__}: {e}")
    raise
