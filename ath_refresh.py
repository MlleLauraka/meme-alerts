"""Weekly ATH tracker refresh: CoinGecko top 100, Oct 2025 cycle-high reference, batch rules."""

from __future__ import annotations

import os
import time
from datetime import datetime, timezone
from typing import Any, Callable

import httpx

from ath_data import BATCH_2X, BATCH_3X_5X, BATCH_GT_5X, CMC_SLUG_BY_TICKER
from ath_db import init_db, save_snapshot, set_meta
from ath_ai_verdict import apply_ai_verdicts
from pipeline import get_api_key_from_env

# Oct 1 2025 00:00:00 UTC — post-Oct 2025 cycle-high window start
OCT_2025_UNIX = int(datetime(2025, 10, 1, tzinfo=timezone.utc).timestamp())

COINGECKO_API_BASE = "https://api.coingecko.com/api/v3"

STABLECOIN_SYMBOLS = {
    "USDT", "USDC", "DAI", "USDE", "FDUSD", "TUSD", "USDD", "PYUSD", "USDS",
    "FRAX", "LUSD", "CRVUSD", "GUSD", "BUSD", "EURC", "USD1", "USDT0", "USD0",
    "USDBC", "USDG", "USDP",
}

COMMODITY_OR_INDEX_SYMBOLS = {"PAXG", "XAUT", "SPX", "SPX6900"}


def _http_client() -> httpx.Client:
    return httpx.Client(timeout=45.0, trust_env=False)


def _coingecko_headers() -> dict[str, str]:
    headers = {"Accept": "application/json"}
    key = os.environ.get("COINGECKO_API_KEY", "").strip()
    if key:
        headers["x-cg-demo-api-key"] = key
    return headers


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _today_iso() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def _is_excluded_symbol(symbol: str) -> bool:
    sym = (symbol or "").upper()
    return sym in STABLECOIN_SYMBOLS or sym in COMMODITY_OR_INDEX_SYMBOLS


def _assign_batch(drawdown_multiple: float | None, symbol: str) -> str | None:
    if _is_excluded_symbol(symbol):
        return None
    if drawdown_multiple is None or drawdown_multiple <= 0:
        return None
    if drawdown_multiple > 5:
        return BATCH_GT_5X
    if drawdown_multiple >= 3:
        return BATCH_3X_5X
    return BATCH_2X


def _pct_to_ath(price: float, ath: float) -> str:
    if ath <= 0 or price <= 0:
        return "n/a"
    pct = (price / ath - 1) * 100
    if pct >= 0:
        return f"+{pct:.0f}%"
    return f"{pct:.0f}%"


def _compute_verdict(price: float, ath: float, batch: str | None, rank: int) -> str:
    if ath <= 0 or price <= 0:
        return "No data"
    ratio = price / ath
    if ratio >= 1.0:
        return "Already exceeded ATH"
    if ratio >= 0.95:
        return "Already near ATH"

    if batch == BATCH_2X:
        if rank <= 20 and ratio >= 0.5:
            return "Likely (bull cycle)"
        if rank <= 50 and ratio >= 0.4:
            return "Likely (bull cycle)"
        if ratio >= 0.33:
            return "Possible"
        return "Unlikely"

    if batch == BATCH_3X_5X:
        if rank <= 25 and ratio >= 0.28:
            return "Likely"
        if ratio >= 0.22:
            return "Possible"
        return "Unlikely"

    if batch == BATCH_GT_5X:
        if rank <= 30 and ratio >= 0.15:
            return "Possible"
        return "Unlikely"

    return "Possible"


def _format_target_2x(ath: float) -> str | None:
    if ath <= 0:
        return None
    target = ath * 2
    return f"~${target:,.0f}" if target >= 1000 else f"~${target:,.4f}"


def _auto_notes(batch: str | None, verdict: str, rank: int, multiple: float | None) -> str:
    parts = [f"CG rank #{rank}"]
    if multiple is not None:
        parts.append(f"{multiple:.1f}× below Oct '25 high")
    if batch:
        parts.append(f"batch: {batch}")
    return " · ".join(parts)


def fetch_coingecko_top100(client: httpx.Client) -> list[dict[str, Any]]:
    resp = client.get(
        f"{COINGECKO_API_BASE}/coins/markets",
        params={
            "vs_currency": "usd",
            "order": "market_cap_desc",
            "per_page": 100,
            "page": 1,
            "sparkline": "false",
        },
        headers=_coingecko_headers(),
    )
    resp.raise_for_status()
    return [
        {
            "coingecko_id": c["id"],
            "ticker": (c.get("symbol") or "").upper(),
            "name": c.get("name") or c["id"],
            "rank": c.get("market_cap_rank") or 999,
            "price_usd": float(c.get("current_price") or 0),
        }
        for c in resp.json()
    ]


def fetch_oct2025_ath_coingecko(client: httpx.Client, coingecko_id: str) -> float | None:
    now = int(datetime.now(timezone.utc).timestamp())
    params = {"vs_currency": "usd", "from": OCT_2025_UNIX, "to": now}
    url = f"{COINGECKO_API_BASE}/coins/{coingecko_id}/market_chart/range"

    for attempt in range(3):
        resp = client.get(url, params=params, headers=_coingecko_headers())
        if resp.status_code == 429:
            time.sleep(15 * (attempt + 1))
            continue
        if resp.status_code != 200:
            return None
        prices = [p[1] for p in resp.json().get("prices", []) if p[1] is not None]
        return max(prices) if prices else None
    return None


def build_asset_row(coin: dict[str, Any], ath_oct2025: float | None) -> dict[str, Any] | None:
    price = coin.get("price_usd") or 0
    ticker = coin["ticker"]
    rank = int(coin.get("rank") or 999)

    if _is_excluded_symbol(ticker):
        return None

    if not ath_oct2025 or ath_oct2025 <= 0:
        return None

    if not price or price <= 0:
        return None

    multiple = ath_oct2025 / price
    batch = _assign_batch(multiple, ticker)
    if not batch:
        return None

    verdict = _compute_verdict(price, ath_oct2025, batch, rank)
    return {
        "cmc_id": None,
        "coingecko_id": coin.get("coingecko_id"),
        "ticker": ticker,
        "name": coin["name"],
        "rank": rank,
        "batch": batch,
        "category": verdict,
        "verdict": verdict,
        "price_usd": price,
        "ath_oct2025": ath_oct2025,
        "drawdown_multiple": round(multiple, 2),
        "pct_to_ath": _pct_to_ath(price, ath_oct2025),
        "target_2x": _format_target_2x(ath_oct2025) if batch == BATCH_2X else None,
        "notes": _auto_notes(batch, verdict, rank, multiple),
        "cmc_slug": CMC_SLUG_BY_TICKER.get(ticker.upper()),
    }


def run_ath_refresh(
    *,
    snapshot_date: str | None = None,
    sleep_seconds: float = 1.5,
    use_ai_verdicts: bool = True,
    on_progress: Callable[[str], None] | None = None,
) -> dict[str, Any]:
    """Fetch CoinGecko top 100, compute Oct 2025 ATH, assign batches, AI verdicts, save."""
    init_db()
    snapshot_date = snapshot_date or _today_iso()
    run_at = _now_iso()
    cg_key = os.environ.get("COINGECKO_API_KEY", "").strip()
    errors: list[str] = []
    assets: list[dict[str, Any]] = []

    with _http_client() as client:
        if on_progress:
            label = "CoinGecko top 100 (with API key)…" if cg_key else "CoinGecko top 100…"
            on_progress(f"Fetching {label}")
        try:
            coins = fetch_coingecko_top100(client)
        except Exception as exc:
            raise RuntimeError(f"CoinGecko top-100 fetch failed: {exc}") from exc

        total = len(coins)
        for i, coin in enumerate(coins, start=1):
            ticker = coin["ticker"]
            cg_id = coin.get("coingecko_id")
            if on_progress:
                on_progress(f"[{i}/{total}] {ticker} — Oct 2025 high…")

            ath = None
            if cg_id:
                try:
                    ath = fetch_oct2025_ath_coingecko(client, cg_id)
                except Exception as exc:
                    errors.append(f"{ticker}: {exc}")
                # Rate limit: slower without demo key, faster with key
                time.sleep(0.6 if cg_key else sleep_seconds)

            row = build_asset_row(coin, ath)
            if row:
                assets.append(row)

    if not assets:
        raise RuntimeError(
            "No assets saved — CoinGecko rate limit or missing price history. "
            "Add a free COINGECKO_API_KEY from coingecko.com/en/api and retry."
        )

    ai_errors: list[str] = []
    verdict_mode = "rules"
    api_key = get_api_key_from_env() if use_ai_verdicts else None
    if api_key:
        if on_progress:
            on_progress(f"Scoring {len(assets)} assets with Claude…")
        assets, ai_errors = apply_ai_verdicts(assets, api_key, on_progress=on_progress)
        verdict_mode = "ai"
        errors.extend(ai_errors)
    elif use_ai_verdicts and on_progress:
        on_progress("No ANTHROPIC_API_KEY — using rule-based verdicts")

    save_snapshot(snapshot_date, run_at, assets)
    set_meta("verdict_mode", verdict_mode)
    return {
        "snapshot_date": snapshot_date,
        "run_at": run_at,
        "count": len(assets),
        "errors": errors[:20],
        "provider": "coingecko",
        "verdict_mode": verdict_mode,
    }
