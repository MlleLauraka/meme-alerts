"""SQLite storage for weekly ATH tracker snapshots and category-change history."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

ATH_DB_PATH = Path(__file__).resolve().parent / "ath_history.db"
META_LAST_REFRESH = "last_refresh_at"
META_LAST_SNAPSHOT = "last_snapshot_date"


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(ATH_DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def db_conn():
    conn = _connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    with db_conn() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS ath_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                snapshot_date TEXT NOT NULL UNIQUE,
                run_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS ath_assets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                snapshot_id INTEGER NOT NULL,
                cmc_id INTEGER,
                coingecko_id TEXT,
                ticker TEXT NOT NULL,
                name TEXT NOT NULL,
                rank INTEGER,
                batch TEXT,
                category TEXT,
                verdict TEXT NOT NULL,
                price_usd REAL,
                ath_oct2025 REAL,
                drawdown_multiple REAL,
                pct_to_ath TEXT,
                target_2x TEXT,
                notes TEXT,
                cmc_slug TEXT,
                FOREIGN KEY (snapshot_id) REFERENCES ath_snapshots(id) ON DELETE CASCADE,
                UNIQUE (snapshot_id, ticker)
            );

            CREATE TABLE IF NOT EXISTS ath_meta (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_ath_assets_snapshot
                ON ath_assets(snapshot_id);
            CREATE INDEX IF NOT EXISTS idx_ath_assets_ticker
                ON ath_assets(ticker);
            """
        )


def set_meta(key: str, value: str) -> None:
    with db_conn() as conn:
        conn.execute(
            "INSERT INTO ath_meta(key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, value),
        )


def get_meta(key: str) -> str | None:
    with db_conn() as conn:
        row = conn.execute("SELECT value FROM ath_meta WHERE key = ?", (key,)).fetchone()
        return row["value"] if row else None


def get_last_refresh() -> dict[str, str | None]:
    return {
        "run_at": get_meta(META_LAST_REFRESH),
        "snapshot_date": get_meta(META_LAST_SNAPSHOT),
    }


def has_live_data() -> bool:
    with db_conn() as conn:
        row = conn.execute("SELECT COUNT(*) AS n FROM ath_snapshots").fetchone()
        return bool(row and row["n"] > 0)


def save_snapshot(snapshot_date: str, run_at: str, assets: list[dict[str, Any]]) -> int:
    init_db()
    with db_conn() as conn:
        conn.execute(
            "INSERT INTO ath_snapshots(snapshot_date, run_at) VALUES (?, ?) "
            "ON CONFLICT(snapshot_date) DO UPDATE SET run_at = excluded.run_at",
            (snapshot_date, run_at),
        )
        snap = conn.execute(
            "SELECT id FROM ath_snapshots WHERE snapshot_date = ?",
            (snapshot_date,),
        ).fetchone()
        snapshot_id = snap["id"]
        conn.execute("DELETE FROM ath_assets WHERE snapshot_id = ?", (snapshot_id,))

        for asset in assets:
            conn.execute(
                """
                INSERT INTO ath_assets (
                    snapshot_id, cmc_id, coingecko_id, ticker, name, rank,
                    batch, category, verdict, price_usd, ath_oct2025,
                    drawdown_multiple, pct_to_ath, target_2x, notes, cmc_slug
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    snapshot_id,
                    asset.get("cmc_id"),
                    asset.get("coingecko_id"),
                    asset["ticker"],
                    asset["name"],
                    asset.get("rank"),
                    asset.get("batch"),
                    asset.get("category"),
                    asset["verdict"],
                    asset.get("price_usd"),
                    asset.get("ath_oct2025"),
                    asset.get("drawdown_multiple"),
                    asset.get("pct_to_ath"),
                    asset.get("target_2x"),
                    asset.get("notes"),
                    asset.get("cmc_slug"),
                ),
            )

    set_meta(META_LAST_REFRESH, run_at)
    set_meta(META_LAST_SNAPSHOT, snapshot_date)
    return snapshot_id


def get_latest_assets() -> list[dict[str, Any]]:
    init_db()
    with db_conn() as conn:
        snap = conn.execute(
            "SELECT id, snapshot_date, run_at FROM ath_snapshots "
            "ORDER BY snapshot_date DESC LIMIT 1"
        ).fetchone()
        if not snap:
            return []
        rows = conn.execute(
            "SELECT * FROM ath_assets WHERE snapshot_id = ? ORDER BY rank ASC, ticker ASC",
            (snap["id"],),
        ).fetchall()
        return [_row_to_asset(r, snap["snapshot_date"]) for r in rows]


def _row_to_asset(row: sqlite3.Row, snapshot_date: str | None = None) -> dict[str, Any]:
    price = row["price_usd"]
    ath = row["ath_oct2025"]
    return {
        "ticker": row["ticker"],
        "name": row["name"],
        "batch": row["batch"] or "",
        "category": row["category"] or row["verdict"],
        "price_jun26": _fmt_price(price),
        "ath": _fmt_price(ath),
        "pct_to_ath": row["pct_to_ath"] or "n/a",
        "verdict": row["verdict"],
        "notes": row["notes"] or "",
        "target_2x": row["target_2x"],
        "rank": row["rank"],
        "drawdown_multiple": row["drawdown_multiple"],
        "snapshot_date": snapshot_date,
        "cmc_slug": row["cmc_slug"],
    }


def _fmt_price(value: float | None) -> str:
    if value is None or value <= 0:
        return "n/a"
    if value >= 1000:
        return f"~${value:,.0f}"
    if value >= 1:
        return f"~${value:,.2f}"
    if value >= 0.01:
        return f"~${value:.4f}"
    return f"~${value:.8f}".rstrip("0").rstrip(".")


def list_snapshots(limit: int = 8) -> list[dict[str, str]]:
    init_db()
    with db_conn() as conn:
        rows = conn.execute(
            "SELECT snapshot_date, run_at FROM ath_snapshots "
            "ORDER BY snapshot_date DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [{"snapshot_date": r["snapshot_date"], "run_at": r["run_at"]} for r in rows]


def get_category_changes(weeks: int = 4) -> list[dict[str, Any]]:
    """Coins whose batch and/or verdict changed across weekly snapshots in the lookback window."""
    init_db()
    cutoff = (datetime.now(timezone.utc) - timedelta(weeks=weeks)).date().isoformat()
    with db_conn() as conn:
        snaps = conn.execute(
            "SELECT id, snapshot_date FROM ath_snapshots "
            "WHERE snapshot_date >= ? ORDER BY snapshot_date ASC",
            (cutoff,),
        ).fetchall()
        if len(snaps) < 2:
            return []

        snap_ids = [s["id"] for s in snaps]
        placeholders = ",".join("?" * len(snap_ids))
        rows = conn.execute(
            f"""
            SELECT snapshot_id, ticker, name, batch, verdict
            FROM ath_assets
            WHERE snapshot_id IN ({placeholders})
            ORDER BY ticker, snapshot_id
            """,
            snap_ids,
        ).fetchall()

    by_ticker: dict[str, list[dict]] = {}
    snap_dates = {s["id"]: s["snapshot_date"] for s in snaps}
    for row in rows:
        by_ticker.setdefault(row["ticker"], []).append(
            {
                "snapshot_date": snap_dates[row["snapshot_id"]],
                "name": row["name"],
                "batch": row["batch"] or "",
                "verdict": row["verdict"],
            }
        )

    changes: list[dict[str, Any]] = []
    first_date = snaps[0]["snapshot_date"]
    last_date = snaps[-1]["snapshot_date"]

    for ticker, history in by_ticker.items():
        if len(history) < 2:
            continue
        earliest = history[0]
        latest = history[-1]
        batch_changed = earliest["batch"] != latest["batch"]
        verdict_changed = earliest["verdict"] != latest["verdict"]
        if not batch_changed and not verdict_changed:
            continue
        changes.append(
            {
                "ticker": ticker,
                "name": latest["name"],
                "from_batch": earliest["batch"] or "—",
                "to_batch": latest["batch"] or "—",
                "from_verdict": earliest["verdict"],
                "to_verdict": latest["verdict"],
                "first_seen": earliest["snapshot_date"],
                "last_seen": latest["snapshot_date"],
                "window_start": first_date,
                "window_end": last_date,
            }
        )

    changes.sort(key=lambda c: (c["to_batch"], c["ticker"]))
    return changes


def get_ticker_history(ticker: str, weeks: int = 4) -> list[dict[str, Any]]:
    init_db()
    cutoff = (datetime.now(timezone.utc) - timedelta(weeks=weeks)).date().isoformat()
    with db_conn() as conn:
        rows = conn.execute(
            """
            SELECT s.snapshot_date, a.batch, a.verdict, a.pct_to_ath, a.drawdown_multiple
            FROM ath_assets a
            JOIN ath_snapshots s ON s.id = a.snapshot_id
            WHERE a.ticker = ? AND s.snapshot_date >= ?
            ORDER BY s.snapshot_date ASC
            """,
            (ticker.upper(), cutoff),
        ).fetchall()
        return [dict(r) for r in rows]
