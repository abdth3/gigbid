"""Durable LangGraph checkpointer (SQLite/Postgres) surviving process restarts (C6)."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

DB_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "processed" / "gigbid_checkpoints.db"

_SYNC_SAVER: SqliteSaver | None = None
_ASYNC_CONN = None
_ASYNC_SAVER: AsyncSqliteSaver | None = None


def get_sync_checkpointer() -> SqliteSaver:
    global _SYNC_SAVER
    if _SYNC_SAVER is None:
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        _SYNC_SAVER = SqliteSaver(conn)
    return _SYNC_SAVER


async def get_async_checkpointer() -> AsyncSqliteSaver:
    global _ASYNC_CONN, _ASYNC_SAVER
    if _ASYNC_SAVER is None:
        import aiosqlite
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        _ASYNC_CONN = await aiosqlite.connect(str(DB_PATH))
        _ASYNC_SAVER = AsyncSqliteSaver(_ASYNC_CONN)
        await _ASYNC_SAVER.setup()
    return _ASYNC_SAVER
