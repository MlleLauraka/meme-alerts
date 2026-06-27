"""Weekly Monday scan → Excel append → 30-day trend analysis."""

from __future__ import annotations

import os
from datetime import date, datetime, timedelta, timezone

import pandas as pd
from dotenv import load_dotenv

from pipeline import (
    AVG_BENCHMARK,
    CHAINS,
    PIPELINE_SCORE_THRESHOLD,
    fetch_dex_pairs,
    get_api_key_from_env,
    log_candidate,
    pre_filter,
    quant_score,
    score_coin_hybrid,
)

load_dotenv()

WEEKLY_REPORT_XLSX = "weekly_report.xlsx"
SHEET_NAME = "snapshots"
MAX_PAIRS_PER_CHAIN = 8
TREND_LOOKBACK_DAYS = 30

REPORT_COLUMNS = [
    "report_date",
    "run_timestamp",
    "ticker",
    "name",
    "chain",
    "pair_address",
    "market_cap_usd",
    "liquidity_usd",
    "volume_24h",
    "vol_mcap_ratio",
    "buyer_sell_ratio",
    "price_change_1h",
    "price_change_6h",
    "price_change_24h",
    "score_total",
    "score_a",
    "score_b",
    "score_c",
    "score_d",
    "score_e",
    "vetoed",
    "veto_fails",
    "verdict",
    "runner_gap",
    "confidence",
    "runner_summary",
    "pair_url",
]


def _verdict_label(total: int, vetoed: bool) -> str:
    if vetoed:
        return "Disqualified"
    if total >= 85:
        return "Strong signal"
    if total >= 70:
        return "Promising"
    if total >= 50:
        return "Speculative"
    return "Do not proceed"


def result_to_report_row(result: dict, report_date: str) -> dict:
    gap = result["total"] - AVG_BENCHMARK
    return {
        "report_date": report_date,
        "run_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "ticker": result.get("ticker", ""),
        "name": result.get("name", ""),
        "chain": result.get("chain", ""),
        "pair_address": result.get("pair_address", ""),
        "market_cap_usd": result.get("market_cap_usd", 0),
        "liquidity_usd": result.get("liquidity_usd", 0),
        "volume_24h": result.get("volume_24h", 0),
        "vol_mcap_ratio": result.get("vol_mcap_ratio", 0),
        "buyer_sell_ratio": result.get("buyer_sell_ratio", 0),
        "price_change_1h": result.get("price_change_1h", 0),
        "price_change_6h": result.get("price_change_6h", 0),
        "price_change_24h": result.get("price_change_24h", 0),
        "score_total": result["total"],
        "score_a": round(result["scores"].get("A", 0)),
        "score_b": round(result["scores"].get("B", 0)),
        "score_c": round(result["scores"].get("C", 0)),
        "score_d": round(result["scores"].get("D", 0)),
        "score_e": round(result["scores"].get("E", 0)),
        "vetoed": result["vetoed"],
        "veto_fails": "|".join(result.get("vetoFails", [])),
        "verdict": _verdict_label(result["total"], result["vetoed"]),
        "runner_gap": gap,
        "confidence": result.get("confidence", ""),
        "runner_summary": result.get("runnerSummary", ""),
        "pair_url": result.get("pair_url", ""),
    }


def append_weekly_report(results: list[dict], report_date: str | None = None) -> int:
    """Append scored rows for one Monday run. Returns rows written."""
    if not results:
        return 0

    report_date = report_date or date.today().isoformat()
    rows = [result_to_report_row(r, report_date) for r in results]
    new_df = pd.DataFrame(rows, columns=REPORT_COLUMNS)

    if os.path.exists(WEEKLY_REPORT_XLSX):
        existing = pd.read_excel(WEEKLY_REPORT_XLSX, sheet_name=SHEET_NAME)
        combined = pd.concat([existing, new_df], ignore_index=True)
    else:
        combined = new_df

    with pd.ExcelWriter(WEEKLY_REPORT_XLSX, engine="openpyxl") as writer:
        combined.to_excel(writer, sheet_name=SHEET_NAME, index=False)
        meta = pd.DataFrame([{
            "last_run": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "rows_appended": len(rows),
            "report_date": report_date,
        }])
        meta.to_excel(writer, sheet_name="meta", index=False)

    return len(rows)


def run_weekly_scan(
    api_key: str | None = None,
    report_date: str | None = None,
    chains: list[str] | None = None,
) -> list[dict]:
    """Scan all chains, score pre-filter passers, append Excel, log strong candidates."""
    api_key = api_key or get_api_key_from_env()
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY required for weekly hybrid scoring")

    report_date = report_date or date.today().isoformat()
    chains = chains or CHAINS
    seen_pairs: set[str] = set()
    results: list[dict] = []

    for chain in chains:
        pairs = fetch_dex_pairs(chain)
        pairs.sort(key=lambda p: p.liquidity_usd, reverse=True)
        passed = []
        for pair in pairs:
            if pair.pair_address in seen_pairs:
                continue
            ok, _ = pre_filter(pair)
            if not ok:
                continue
            seen_pairs.add(pair.pair_address)
            passed.append(pair)
            if len(passed) >= MAX_PAIRS_PER_CHAIN:
                break

        for pair in passed:
            quant = quant_score(pair)
            result = score_coin_hybrid(pair, quant, api_key=api_key)
            if not result:
                continue
            results.append(result)
            if result["total"] >= PIPELINE_SCORE_THRESHOLD:
                log_candidate(result)

    append_weekly_report(results, report_date)
    return results


def load_snapshots(days: int = TREND_LOOKBACK_DAYS) -> pd.DataFrame:
    if not os.path.exists(WEEKLY_REPORT_XLSX):
        return pd.DataFrame(columns=REPORT_COLUMNS)

    df = pd.read_excel(WEEKLY_REPORT_XLSX, sheet_name=SHEET_NAME)
    if df.empty:
        return df

    df["report_date"] = pd.to_datetime(df["report_date"]).dt.normalize()
    cutoff = pd.Timestamp.now().normalize() - pd.Timedelta(days=days)
    return df[df["report_date"] >= cutoff].copy()


def compute_trends(df: pd.DataFrame) -> pd.DataFrame:
    """Per-token trend summary over the snapshot window."""
    if df.empty:
        return pd.DataFrame()

    trends = []
    for (ticker, chain), group in df.groupby(["ticker", "chain"]):
        group = group.sort_values("report_date")
        appearances = len(group)
        first = group.iloc[0]
        last = group.iloc[-1]
        score_first = int(first["score_total"])
        score_latest = int(last["score_total"])
        score_delta = score_latest - score_first
        scores = [int(s) for s in group["score_total"].tolist()]
        dates = [d.strftime("%Y-%m-%d") for d in group["report_date"]]

        improving_weeks = sum(
            1 for i in range(1, len(scores)) if scores[i] > scores[i - 1]
        )

        trend = "New"
        if appearances >= 2:
            if improving_weeks == appearances - 1:
                trend = "Streak up"
            elif score_delta >= 8:
                trend = "Strong rise"
            elif score_delta >= 3:
                trend = "Rising"
            elif score_delta <= -8:
                trend = "Falling"
            elif score_delta <= -3:
                trend = "Softening"
            else:
                trend = "Stable"

        trending = appearances >= 2 and score_delta >= 3
        near_breakout = score_latest >= 65 and score_delta >= 2

        trends.append({
            "ticker": ticker,
            "chain": chain,
            "name": last.get("name", ""),
            "appearances": appearances,
            "first_seen": first["report_date"].strftime("%Y-%m-%d"),
            "last_seen": last["report_date"].strftime("%Y-%m-%d"),
            "score_first": score_first,
            "score_latest": score_latest,
            "score_delta": score_delta,
            "improving_weeks": improving_weeks,
            "trend": trend,
            "trending": trending,
            "near_breakout": near_breakout,
            "verdict_latest": last.get("verdict", ""),
            "market_cap_usd": last.get("market_cap_usd", 0),
            "pair_url": last.get("pair_url", ""),
            "score_history": scores,
            "date_history": dates,
        })

    out = pd.DataFrame(trends)
    if out.empty:
        return out
    return out.sort_values(
        ["trending", "near_breakout", "score_delta", "appearances"],
        ascending=[False, False, False, False],
    ).reset_index(drop=True)


def get_report_meta() -> dict:
    if not os.path.exists(WEEKLY_REPORT_XLSX):
        return {}
    try:
        meta = pd.read_excel(WEEKLY_REPORT_XLSX, sheet_name="meta")
        if meta.empty:
            return {}
        return meta.iloc[-1].to_dict()
    except Exception:
        return {}
