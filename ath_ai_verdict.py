"""AI verdict scoring for ATH tracker batches (Claude)."""

from __future__ import annotations

import json
import re
from typing import Any, Callable

import anthropic

from ath_data import BATCH_2X, BATCH_3X_5X, BATCH_GT_5X
from pipeline import make_anthropic_client

VALID_VERDICTS = {
    "Already exceeded ATH",
    "Already near ATH",
    "Likely (bull cycle)",
    "Likely",
    "Possible",
    "Unlikely",
    "No data",
}

ATH_VERDICT_SYSTEM = """You are a crypto macro analyst scoring top-100 assets against their
post-October 2025 cycle-high (ATH reference = highest price since 1 Oct 2025).

Assign exactly one verdict per ticker from this list ONLY:
- Already exceeded ATH
- Already near ATH
- Likely (bull cycle)
- Likely
- Possible
- Unlikely
- No data

Batch meanings (already assigned — do not change batch):
- "Top 100 3x-5x": token is 3×–5× below Oct 2025 high. Score likelihood of reaching
  at least that Oct 2025 ATH again in a future cycle.
- "Top 100 >5x": token is >5× below Oct 2025 high. Score likelihood of recovering
  to at least the Oct 2025 ATH.
- "2x +potential ATH": token is <3× below Oct 2025 high (not a stablecoin). Score
  likelihood of eventually doubling the Oct 2025 ATH (2× that high).

Use "Likely (bull cycle)" mainly for batch "2x +potential ATH" on large-cap leaders
(BTC, ETH, etc.) when a doubled Oct ATH is plausible in a bull cycle.
Use "Likely" for recovery batches when Oct ATH revisit is structurally plausible.

Context: June 2026, ~26 months post-Bitcoin halving (Apr 2024). Meme/speculative
risk appetite is subdued but institutional adoption continues on majors.

Respond ONLY with a JSON array. No markdown fences. Each item:
{"ticker":"SYMBOL","verdict":"...","note":"one concise sentence"}
"""


def _chunk(items: list[Any], size: int) -> list[list[Any]]:
    return [items[i : i + size] for i in range(0, len(items), size)]


def _normalize_verdict(raw: str, batch: str) -> str:
    v = (raw or "").strip()
    if v in VALID_VERDICTS:
        return v
    lower = v.lower()
    mapping = {
        "exceeded": "Already exceeded ATH",
        "near ath": "Already near ATH",
        "bull cycle": "Likely (bull cycle)",
        "likely": "Likely" if batch != BATCH_2X else "Likely (bull cycle)",
        "possible": "Possible",
        "unlikely": "Unlikely",
    }
    for key, val in mapping.items():
        if key in lower:
            return val
    return "Possible"


def _build_user_prompt(chunk: list[dict[str, Any]]) -> str:
    lines = [
        "Score these assets. Use the batch field to apply the correct framing.",
        "",
    ]
    for a in chunk:
        lines.append(
            f"- {a['ticker']} ({a['name']}) · batch: {a['batch']} · "
            f"rank #{a['rank']} · price ${a['price_usd']:,.4f} · "
            f"Oct2025_high ${a['ath_oct2025']:,.4f} · "
            f"{a['drawdown_multiple']:.1f}× below high · {a['pct_to_ath']} vs ATH"
            + (f" · 2x target {a['target_2x']}" if a.get("target_2x") else "")
        )
    return "\n".join(lines)


def _parse_ai_response(raw: str) -> list[dict[str, str]]:
    clean = re.sub(r"```json|```", "", raw).strip()
    data = json.loads(clean)
    if not isinstance(data, list):
        raise ValueError("Expected JSON array")
    return data


def apply_ai_verdicts(
    assets: list[dict[str, Any]],
    api_key: str,
    *,
    chunk_size: int = 10,
    on_progress: Callable[[str], None] | None = None,
) -> tuple[list[dict[str, Any]], list[str]]:
    """Return assets with AI verdict + note merged; falls back per-row on parse errors."""
    if not assets:
        return assets, []

    client = make_anthropic_client(api_key)
    errors: list[str] = []
    by_ticker = {a["ticker"].upper(): a for a in assets}
    chunks = _chunk(assets, chunk_size)

    for idx, chunk in enumerate(chunks, start=1):
        if on_progress:
            tickers = ", ".join(a["ticker"] for a in chunk[:4])
            suffix = "…" if len(chunk) > 4 else ""
            on_progress(f"AI verdicts [{idx}/{len(chunks)}]: {tickers}{suffix}")

        try:
            message = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=2000,
                system=ATH_VERDICT_SYSTEM,
                messages=[{"role": "user", "content": _build_user_prompt(chunk)}],
            )
            rows = _parse_ai_response(message.content[0].text)
        except (json.JSONDecodeError, KeyError, IndexError, anthropic.APIError) as exc:
            errors.append(f"AI chunk {idx}: {exc}")
            continue

        for row in rows:
            ticker = (row.get("ticker") or "").upper()
            asset = by_ticker.get(ticker)
            if not asset:
                continue
            verdict = _normalize_verdict(row.get("verdict", ""), asset.get("batch", ""))
            note = (row.get("note") or "").strip()
            rule_verdict = asset.get("verdict")
            asset["verdict"] = verdict
            asset["category"] = verdict
            base = note or f"AI verdict (was {rule_verdict})"
            rank = asset.get("rank")
            mult = asset.get("drawdown_multiple")
            asset["notes"] = (
                f"{base} · rank #{rank} · {mult:.1f}× below Oct '25 high"
                if mult is not None
                else base
            )

    return assets, errors
