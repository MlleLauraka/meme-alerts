import csv
import json
import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable
from urllib.parse import quote

import anthropic
import httpx
from dotenv import load_dotenv

from ath_data import is_excluded_from_analysis

load_dotenv()

DEXSCREENER_API = "https://api.dexscreener.com"
SEARCH_RESULT_LIMIT = 20
EVM_ADDRESS_RE = re.compile(r"^0x[a-fA-F0-9]{40}$")
SOLANA_ADDRESS_RE = re.compile(r"^[1-9A-HJ-NP-Za-km-z]{32,44}$")
CHAIN_PREFIX_RE = re.compile(
    r"^(solana|ethereum|base|bsc|arbitrum|polygon|optimism|avax)"
    r"[/:\s]+(.+)$",
    re.IGNORECASE,
)
PAIR_LOOKUP_CHAINS = [
    "solana", "ethereum", "base", "bsc", "arbitrum", "polygon", "optimism", "avax",
]

# ── Pipeline config ──────────────────────────────────────────────────────────
CHAINS = ["solana", "ethereum", "base", "bsc"]
MIN_LIQUIDITY_USD = 100_000
MCAP_MIN = 5_000_000
MCAP_MAX = 50_000_000
TOKEN_AGE_MIN_HOURS = 24
TOKEN_AGE_MAX_HOURS = 168
MIN_BUYER_SELL_RATIO = 1.2
MIN_VOL_MCAP_RATIO = 0.10
POLL_INTERVAL_SECS = 300
PIPELINE_SCORE_THRESHOLD = 70
CANDIDATES_CSV = "candidates.csv"
AVG_BENCHMARK = 81

CSV_COLUMNS = [
    "timestamp", "ticker", "name", "chain", "pair_address",
    "current_mcap", "liquidity_usd", "volume_24h", "vol_mcap_ratio",
    "buyer_sell_ratio", "price_change_1h", "price_change_6h", "price_change_24h",
    "score_total", "score_a", "score_b", "score_c", "score_d", "score_e",
    "vetoed", "veto_fails", "verdict", "runner_gap",
    "confidence", "runner_summary", "pair_url",
]

HYBRID_SYSTEM_PROMPT = """You are the Memecoin Runner Indicator engine scoring
a token that has already passed on-chain pre-filters and has quantitative
scores pre-computed for sections C and E1.

YOU MUST ONLY SCORE:
- Section A (meme foundation, 25pts): A1=pre-existing meme recognition(10), A2=emotional charge(8), A3=remixability(7)
- Section B (token structure, 25pts): B1=LP burned/locked(8), B2=contract renounced(7), B3=supply distribution(10)
- Section D (cycle and meta fit, 15pts): D1=BTC halving proximity(7), D2=archetype novelty(8)
- Section E2 ONLY (organic influencer pickup, 4pts)
- All 6 veto checks

DO NOT re-score C1, C2, C3, or E1 — they are provided from on-chain data.

Veto checks (any fail = disqualify regardless of score):
V1: LP burned or locked, V2: zero buy/sell tax, V3: no presale/VC allocation,
V4: no utility/roadmap promised, V5: team wallet under 10% of supply,
V6: meme predates the token

The current date is June 2026. Bitcoin's last halving was April 2024.
We are ~26 months post-halving — a subdued phase for memes. Next halving ~April 2028.

Respond ONLY with a valid JSON object. No preamble, no markdown fences:
{
  "scores": {"A": 0, "B": 0, "D": 0, "E2": 0},
  "breakdown": {"A1":0,"A2":0,"A3":0,"B1":0,"B2":0,"B3":0,"D1":0,"D2":0,"E2":0},
  "vetoFails": [],
  "findings": [{"icon": "+"|"~"|"x", "text": "..."}],
  "runnerSummary": "2-3 sentences",
  "confidence": "high|medium|low",
  "confidenceNote": "..."
}"""


def make_anthropic_client(api_key: str) -> anthropic.Anthropic:
    return anthropic.Anthropic(
        api_key=api_key,
        http_client=httpx.Client(trust_env=False, timeout=120.0),
    )


def get_api_key_from_env() -> str | None:
    return os.environ.get("ANTHROPIC_API_KEY")


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


def _http_get_json(url: str) -> dict | list | None:
    try:
        with httpx.Client(trust_env=False, timeout=30.0) as client:
            response = client.get(url)
            response.raise_for_status()
            return response.json()
    except Exception:
        return None


def _safe_float(value, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_int(value, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _parse_created_at(raw) -> datetime:
    if raw is None:
        return datetime.now(timezone.utc)
    try:
        ts = float(raw)
        if ts > 1_000_000_000_000:
            ts /= 1000.0
        return datetime.fromtimestamp(ts, tz=timezone.utc)
    except (TypeError, ValueError, OSError):
        return datetime.now(timezone.utc)


@dataclass
class DexPair:
    pair_address: str
    token_name: str
    token_symbol: str
    chain_id: str
    dex_id: str
    price_usd: float
    market_cap: float
    liquidity_usd: float
    volume_24h: float
    price_change_5m: float
    price_change_1h: float
    price_change_6h: float
    price_change_24h: float
    txns_24h_buys: int
    txns_24h_sells: int
    created_at: datetime
    pair_url: str

    @property
    def buyer_sell_ratio(self) -> float:
        return self.txns_24h_buys / max(self.txns_24h_sells, 1)


def _pair_from_api(raw: dict) -> DexPair | None:
    if not raw:
        return None
    base = raw.get("baseToken") or {}
    quote = raw.get("quoteToken") or {}
    liquidity = raw.get("liquidity") or {}
    volume = raw.get("volume") or {}
    price_change = raw.get("priceChange") or {}
    txns = (raw.get("txns") or {}).get("h24") or {}

    chain_id = raw.get("chainId") or ""
    pair_address = raw.get("pairAddress") or ""
    if not chain_id or not pair_address:
        return None

    pair_url = raw.get("url") or f"https://dexscreener.com/{chain_id}/{pair_address}"
    market_cap = _safe_float(raw.get("marketCap"))
    if market_cap <= 0:
        market_cap = _safe_float(raw.get("fdv"))

    return DexPair(
        pair_address=pair_address,
        token_name=base.get("name") or quote.get("name") or "Unknown",
        token_symbol=(base.get("symbol") or quote.get("symbol") or "?").upper(),
        chain_id=chain_id,
        dex_id=raw.get("dexId") or "",
        price_usd=_safe_float(raw.get("priceUsd")),
        market_cap=market_cap,
        liquidity_usd=_safe_float(liquidity.get("usd")),
        volume_24h=_safe_float(volume.get("h24")),
        price_change_5m=_safe_float(price_change.get("m5")),
        price_change_1h=_safe_float(price_change.get("h1")),
        price_change_6h=_safe_float(price_change.get("h6")),
        price_change_24h=_safe_float(price_change.get("h24")),
        txns_24h_buys=_safe_int(txns.get("buys")),
        txns_24h_sells=_safe_int(txns.get("sells")),
        created_at=_parse_created_at(raw.get("pairCreatedAt")),
        pair_url=pair_url,
    )


def _dedupe_pairs(pairs: list["DexPair"]) -> list["DexPair"]:
    seen: set[str] = set()
    unique: list[DexPair] = []
    for pair in pairs:
        if pair.pair_address in seen:
            continue
        seen.add(pair.pair_address)
        unique.append(pair)
    return unique


def _extract_raw_pairs(payload: dict | list | None) -> list[dict]:
    if not payload:
        return []
    if isinstance(payload, list):
        return [p for p in payload if isinstance(p, dict)]
    if isinstance(payload, dict):
        pairs = payload.get("pairs")
        if isinstance(pairs, list):
            return [p for p in pairs if isinstance(p, dict)]
    return []


def _raw_pairs_to_dex_pairs(raw_pairs: list[dict]) -> list[DexPair]:
    pairs: list[DexPair] = []
    for raw in raw_pairs:
        pair = _pair_from_api(raw)
        if pair:
            pairs.append(pair)
    return pairs


def _protocol_slug(query: str) -> str:
    slug = query.strip().lower().replace("_", "-")
    slug = re.sub(r"[^a-z0-9-]+", "-", slug)
    return re.sub(r"-+", "-", slug).strip("-")


def _fetch_pairs_from_url(url: str) -> list[DexPair]:
    payload = _http_get_json(url)
    return _raw_pairs_to_dex_pairs(_extract_raw_pairs(payload))


def _fetch_pairs_by_token_address(address: str) -> list[DexPair]:
    return _fetch_pairs_from_url(f"{DEXSCREENER_API}/latest/dex/tokens/{quote(address, safe='')}")


def _fetch_pairs_by_chain_token(chain: str, address: str) -> list[DexPair]:
    chain = chain.lower()
    addr = quote(address.strip(), safe="")
    pairs = _fetch_pairs_from_url(f"{DEXSCREENER_API}/token-pairs/v1/{chain}/{addr}")
    if pairs:
        return pairs
    return _fetch_pairs_from_url(f"{DEXSCREENER_API}/latest/dex/pairs/{chain}/{addr}")


def _fetch_pairs_by_pair_address(address: str) -> list[DexPair]:
    addr = quote(address.strip(), safe="")
    found: list[DexPair] = []
    for chain in PAIR_LOOKUP_CHAINS:
        found.extend(
            _fetch_pairs_from_url(f"{DEXSCREENER_API}/latest/dex/pairs/{chain}/{addr}")
        )
        if found:
            break
    return found


def _fetch_pairs_by_search(query: str) -> list[DexPair]:
    q = quote(query.strip())
    return _fetch_pairs_from_url(f"{DEXSCREENER_API}/latest/dex/search?q={q}")


def _fetch_pairs_by_protocol_slug(slug: str) -> list[DexPair]:
    if not slug:
        return []
    return _fetch_pairs_from_url(f"{DEXSCREENER_API}/metas/meta/v1/{quote(slug, safe='')}")


def search_dex_pairs(query: str, on_warning: Callable[[str], None] | None = None) -> list[DexPair]:
    """Resolve DexScreener pairs by protocol slug, token name/symbol, or contract address."""
    q = (query or "").strip()
    if not q:
        return []

    try:
        pairs: list[DexPair] = []
        chain_match = CHAIN_PREFIX_RE.match(q)

        if chain_match:
            chain, address = chain_match.group(1).lower(), chain_match.group(2).strip()
            pairs.extend(_fetch_pairs_by_chain_token(chain, address))
        elif EVM_ADDRESS_RE.match(q):
            pairs.extend(_fetch_pairs_by_token_address(q))
            if not pairs:
                pairs.extend(_fetch_pairs_by_pair_address(q))
        elif len(q) >= 32 and SOLANA_ADDRESS_RE.match(q):
            pairs.extend(_fetch_pairs_by_token_address(q))
            if not pairs:
                pairs.extend(_fetch_pairs_by_pair_address(q))
        else:
            pairs.extend(_fetch_pairs_by_search(q))
            slug = _protocol_slug(q)
            if slug:
                pairs.extend(_fetch_pairs_by_protocol_slug(slug))

        pairs = _dedupe_pairs(pairs)
        pairs.sort(key=lambda p: p.liquidity_usd, reverse=True)
        return pairs[:SEARCH_RESULT_LIMIT]
    except Exception as exc:
        if on_warning:
            on_warning(f"DexScreener search failed for '{query}': {exc}")
        return []


def fetch_dex_pairs(chain: str, on_warning: Callable[[str], None] | None = None) -> list[DexPair]:
    pairs: list[DexPair] = []
    urls = [
        f"{DEXSCREENER_API}/latest/dex/search?q={quote(chain + ' meme')}",
        f"{DEXSCREENER_API}/latest/dex/search?q={quote(chain)}",
    ]

    try:
        for url in urls:
            for raw in _extract_raw_pairs(_http_get_json(url)):
                if (raw.get("chainId") or "").lower() != chain.lower():
                    continue
                pair = _pair_from_api(raw)
                if pair:
                    pairs.append(pair)
    except Exception as exc:
        if on_warning:
            on_warning(f"DexScreener fetch failed for {chain}: {exc}")
        return []

    return _dedupe_pairs(pairs)


def pre_filter(pair: DexPair) -> tuple[bool, str]:
    if is_excluded_from_analysis(pair.token_symbol, pair.token_name):
        return False, "Stablecoin / RWA — excluded from analysis"

    if pair.liquidity_usd < MIN_LIQUIDITY_USD:
        return False, f"Liquidity ${pair.liquidity_usd:,.0f} below ${MIN_LIQUIDITY_USD:,.0f} min"

    if not (MCAP_MIN <= pair.market_cap <= MCAP_MAX):
        return False, f"Mcap ${pair.market_cap:,.0f} outside $5M–$50M window"

    age_hours = (datetime.now(timezone.utc) - pair.created_at).total_seconds() / 3600
    if not (TOKEN_AGE_MIN_HOURS <= age_hours <= TOKEN_AGE_MAX_HOURS):
        return False, f"Token age {age_hours:.1f}h outside 24h–168h window"

    if pair.buyer_sell_ratio < MIN_BUYER_SELL_RATIO:
        return False, f"Buy/sell ratio {pair.buyer_sell_ratio:.2f} below {MIN_BUYER_SELL_RATIO} min"

    momentum_checks = [
        pair.price_change_1h > 5.0,
        pair.price_change_6h > 10.0,
        pair.price_change_24h > 20.0,
    ]
    if sum(momentum_checks) < 2:
        return False, (
            f"Insufficient momentum — "
            f"1h={pair.price_change_1h:.1f}% "
            f"6h={pair.price_change_6h:.1f}% "
            f"24h={pair.price_change_24h:.1f}%"
        )

    vol_mcap = pair.volume_24h / max(pair.market_cap, 1)
    if vol_mcap < MIN_VOL_MCAP_RATIO:
        return False, f"Vol/mcap {vol_mcap:.1%} below {MIN_VOL_MCAP_RATIO:.0%} min"

    return True, ""


def summarize_pre_filter(pairs: list[DexPair]) -> list[dict]:
    """Return per-pair pass/fail details for UI display."""
    rows = []
    for pair in pairs:
        passed, reason = pre_filter(pair)
        age_hours = (datetime.now(timezone.utc) - pair.created_at).total_seconds() / 3600
        rows.append({
            "symbol": pair.token_symbol,
            "chain": pair.chain_id,
            "market_cap": pair.market_cap,
            "liquidity_usd": pair.liquidity_usd,
            "age_hours": age_hours,
            "buyer_sell_ratio": pair.buyer_sell_ratio,
            "vol_mcap_ratio": pair.volume_24h / max(pair.market_cap, 1),
            "price_change_1h": pair.price_change_1h,
            "price_change_6h": pair.price_change_6h,
            "price_change_24h": pair.price_change_24h,
            "passed": passed,
            "reason": reason or "Passed all gates",
            "pair_url": pair.pair_url,
        })
    return rows


def quant_score(pair: DexPair) -> dict:
    buys = pair.txns_24h_buys
    if buys >= 500:
        c1 = 10.0
    elif buys >= 200:
        c1 = 7.0
    elif buys >= 100:
        c1 = 5.0
    elif buys >= 50:
        c1 = 3.0
    else:
        c1 = 0.0
    c1_evidence = f"Buy txns 24h: {buys}"

    ratio = pair.volume_24h / max(pair.market_cap, 1)
    if ratio >= 0.30:
        c2 = 8.0
    elif ratio >= 0.15:
        c2 = 5.0
    elif ratio >= 0.10:
        c2 = 3.0
    else:
        c2 = 0.0
    c2_evidence = f"Vol/mcap: {ratio:.1%}"

    bsr = pair.buyer_sell_ratio
    if bsr >= 2.0:
        c3 = 7.0
    elif bsr >= 1.5:
        c3 = 5.0
    elif bsr >= 1.2:
        c3 = 3.0
    else:
        c3 = 0.0
    c3_evidence = f"Buy/sell ratio: {bsr:.2f}"

    m5 = pair.price_change_5m
    m1h = pair.price_change_1h
    m6h = pair.price_change_6h
    m24 = pair.price_change_24h
    if m5 > 5 and m1h > 20:
        e1 = 6.0
    elif m1h > 10 and m6h > 25:
        e1 = 5.0
    elif m1h > 5 and m24 > 20:
        e1 = 4.0
    elif m24 > 10:
        e1 = 2.0
    else:
        e1 = 0.0
    e1_evidence = f"5m={m5:.1f}% 1h={m1h:.1f}% 6h={m6h:.1f}% 24h={m24:.1f}%"

    return {
        "scores": {"C": c1 + c2 + c3, "E_partial": e1},
        "breakdown": {"C1": c1, "C2": c2, "C3": c3, "E1": e1},
        "evidence": {
            "C1": c1_evidence,
            "C2": c2_evidence,
            "C3": c3_evidence,
            "E1": e1_evidence,
        },
    }


def score_coin_hybrid(pair: DexPair, quant: dict, api_key: str | None = None) -> dict | None:
    api_key = api_key or get_api_key_from_env()
    if not api_key:
        return None

    evidence_block = "\n".join(f"  {k}: {v}" for k, v in quant["evidence"].items())
    user_msg = (
        f"Token: {pair.token_symbol} ({pair.token_name}) on {pair.chain_id}\n"
        f"Pair: {pair.pair_address}\n"
        f"Mcap: ${pair.market_cap:,.0f} | Liquidity: ${pair.liquidity_usd:,.0f}\n"
        f"Pre-computed on-chain scores:\n{evidence_block}\n\n"
        f"Score sections A, B, D, E2, and all veto checks."
    )

    try:
        client = make_anthropic_client(api_key)
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1000,
            system=HYBRID_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_msg}],
        )
        raw = message.content[0].text
        clean = re.sub(r"```json|```", "", raw).strip()
        ai = json.loads(clean)
    except Exception:
        return None

    merged_scores = {
        "A": ai["scores"].get("A", 0),
        "B": ai["scores"].get("B", 0),
        "C": quant["scores"]["C"],
        "D": ai["scores"].get("D", 0),
        "E": quant["scores"]["E_partial"] + ai["scores"].get("E2", 0),
    }
    total = round(sum(merged_scores.values()))
    vetoed = len(ai.get("vetoFails", [])) > 0

    return {
        "query": pair.token_symbol,
        "name": pair.token_name,
        "ticker": pair.token_symbol,
        "chain": pair.chain_id,
        "launched": pair.created_at.strftime("%b %Y"),
        "currentMcap": f"~${pair.market_cap / 1e6:.1f}M",
        "athMcap": "Unknown",
        "scores": merged_scores,
        "breakdown": {**quant["breakdown"], **ai.get("breakdown", {})},
        "vetoFails": ai.get("vetoFails", []),
        "findings": ai.get("findings", []),
        "runnerSummary": ai.get("runnerSummary", ""),
        "confidence": ai.get("confidence", "medium"),
        "confidenceNote": ai.get("confidenceNote", ""),
        "total": total,
        "vetoed": vetoed,
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "pair_address": pair.pair_address,
        "pair_url": pair.pair_url,
        "liquidity_usd": pair.liquidity_usd,
        "volume_24h": pair.volume_24h,
        "vol_mcap_ratio": pair.volume_24h / max(pair.market_cap, 1),
        "buyer_sell_ratio": pair.buyer_sell_ratio,
        "price_change_1h": pair.price_change_1h,
        "price_change_6h": pair.price_change_6h,
        "price_change_24h": pair.price_change_24h,
        "scoring_method": "hybrid",
        "market_cap_usd": pair.market_cap,
    }


def log_candidate(result: dict) -> bool:
    exists: set[tuple[str, str]] = set()
    if os.path.exists(CANDIDATES_CSV):
        with open(CANDIDATES_CSV, newline="") as f:
            for row in csv.DictReader(f):
                exists.add((row["ticker"], row["chain"]))

    key = (result.get("ticker", ""), result.get("chain", ""))
    if key in exists:
        return False

    verdict_text = _verdict_label(result["total"], result["vetoed"])
    gap = result["total"] - AVG_BENCHMARK

    row = {
        "timestamp": result.get("timestamp", ""),
        "ticker": result.get("ticker", ""),
        "name": result.get("name", ""),
        "chain": result.get("chain", ""),
        "pair_address": result.get("pair_address", ""),
        "current_mcap": result.get("currentMcap", ""),
        "liquidity_usd": f"{result.get('liquidity_usd', 0):,.0f}",
        "volume_24h": f"{result.get('volume_24h', 0):,.0f}",
        "vol_mcap_ratio": f"{result.get('vol_mcap_ratio', 0):.1%}",
        "buyer_sell_ratio": f"{result.get('buyer_sell_ratio', 0):.2f}",
        "price_change_1h": f"{result.get('price_change_1h', 0):.1f}%",
        "price_change_6h": f"{result.get('price_change_6h', 0):.1f}%",
        "price_change_24h": f"{result.get('price_change_24h', 0):.1f}%",
        "score_total": result["total"],
        "score_a": round(result["scores"].get("A", 0)),
        "score_b": round(result["scores"].get("B", 0)),
        "score_c": round(result["scores"].get("C", 0)),
        "score_d": round(result["scores"].get("D", 0)),
        "score_e": round(result["scores"].get("E", 0)),
        "vetoed": result["vetoed"],
        "veto_fails": "|".join(result.get("vetoFails", [])),
        "verdict": verdict_text,
        "runner_gap": f"{'+' if gap >= 0 else ''}{gap}",
        "confidence": result.get("confidence", ""),
        "runner_summary": result.get("runnerSummary", ""),
        "pair_url": result.get("pair_url", ""),
    }

    write_header = not os.path.exists(CANDIDATES_CSV)
    with open(CANDIDATES_CSV, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        if write_header:
            writer.writeheader()
        writer.writerow(row)
    return True


def load_candidates(n: int = 100) -> list[dict]:
    if not os.path.exists(CANDIDATES_CSV):
        return []
    with open(CANDIDATES_CSV, newline="") as f:
        rows = list(csv.DictReader(f))
    filtered = [
        r for r in rows
        if not is_excluded_from_analysis(r.get("ticker"), r.get("name"))
    ]
    return list(reversed(filtered[-n:]))


def parse_liquidity_usd(value: str | float | int) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    return float(str(value).replace(",", "") or 0)
