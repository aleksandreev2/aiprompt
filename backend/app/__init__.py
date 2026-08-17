"""Application components for NovelAI Prompt Lab.

Gradio creates the global knowledge base during module import, then executes UI
callbacks in worker threads. Python's sqlite3 connections are thread-affine by
default, so the in-memory FTS5 index must opt out of that affinity.

This compatibility shim is intentionally narrow: it changes only ``:memory:``
connections that did not explicitly choose a ``check_same_thread`` policy.
"""
from __future__ import annotations

import sqlite3 as _sqlite3

_original_sqlite_connect = _sqlite3.connect


def _gradio_safe_sqlite_connect(database, *args, **kwargs):
    if str(database) == ":memory:" and "check_same_thread" not in kwargs:
        kwargs["check_same_thread"] = False
    return _original_sqlite_connect(database, *args, **kwargs)


_sqlite3.connect = _gradio_safe_sqlite_connect
