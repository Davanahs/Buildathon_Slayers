"""
Database connection helpers for the AI Router System.

Single source of truth for all DB access. Every module imports from here
instead of creating its own connection logic.
"""

import os
from typing import Any, Dict, List, Optional

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")


def get_conn():
    """Return a new psycopg2 connection. Caller is responsible for closing it."""
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL is not set in .env")
    return psycopg2.connect(DATABASE_URL)


def fetch_one(query: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
    """Execute a query and return the first row as a dict, or None."""
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query, params)
            row = cur.fetchone()
            return dict(row) if row else None


def fetch_all(query: str, params: tuple = ()) -> List[Dict[str, Any]]:
    """Execute a query and return all rows as a list of dicts."""
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query, params)
            return [dict(r) for r in cur.fetchall()]


def execute(query: str, params: tuple = ()) -> None:
    """Execute a write query (INSERT/UPDATE/DELETE) and commit."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
        conn.commit()


def execute_many(query: str, params_list: List[tuple]) -> None:
    """Execute a write query for multiple parameter sets and commit."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.executemany(query, params_list)
        conn.commit()
