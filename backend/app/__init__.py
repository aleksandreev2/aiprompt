"""Application components for NovelAI Prompt Lab.

Gradio creates the global knowledge base during module import, then executes UI
callbacks in worker threads. Python's sqlite3 connections are thread-affine by
default, while one shared SQLite connection also must not be used concurrently.

This compatibility shim is intentionally narrow: it affects only ``:memory:``
connections that did not explicitly choose a ``check_same_thread`` policy, and it
serializes only KnowledgeBase FTS queries. Exact aliases and the rest of the app
remain untouched.
"""
from __future__ import annotations

import sqlite3 as _sqlite3
import threading as _threading

_original_sqlite_connect = _sqlite3.connect


def _gradio_safe_sqlite_connect(database, *args, **kwargs):
    if str(database) == ":memory:" and "check_same_thread" not in kwargs:
        kwargs["check_same_thread"] = False
    return _original_sqlite_connect(database, *args, **kwargs)


_sqlite3.connect = _gradio_safe_sqlite_connect

# Import the knowledge module after the SQLite connection policy is installed.
# This package __init__ runs before callers receive backend.app.knowledge.
from . import knowledge as _knowledge  # noqa: E402

_fts_query_lock = _threading.RLock()
_original_fts_hits = _knowledge.KnowledgeBase._fts_hits


def _serialized_fts_hits(self, *args, **kwargs):
    with _fts_query_lock:
        return _original_fts_hits(self, *args, **kwargs)


_knowledge.KnowledgeBase._fts_hits = _serialized_fts_hits
