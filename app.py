"""Compatibility entrypoint.

Use START.bat on Windows. This file simply delegates to the robust launcher.
"""
from launcher import main

if __name__ == "__main__":
    raise SystemExit(main())
