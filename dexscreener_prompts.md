# DexScreener pipeline — Cursor prompts

Built from your actual app.py. Send these to Cursor in order.
Each prompt references the exact functions, variable names, and patterns already in your file.

---

## Context Cursor needs to know before you start

- Single file: `app.py` (~639 lines)
- API client pattern: `make_anthropic_client()` using `httpx.Client(trust_env=False)` — keep this pattern for DexScreener too
- Session state pattern: `st.session_state.history`, `st.session_state.current_result` — extend, don't replace
- Config lives inline as constants (BENCHMARKS, AVG_BENCHMARK, etc.) — add pipeline config the same way
- API key retrieved via `get_api_key()` — already handles env, .env, sidebar, secrets
- `.env` file supported via `python-dotenv` — already in requirements.txt
- `run.sh` clears proxy vars — DexScreener calls will work without changes

---

## Prompt 1 — Pipeline constants and DexPair dataclass

```
In app.py, after the BENCHMARKS and AVG_BENCHMARK constants (around line 111),
add a pipeline configuration block and a DexPair dataclass.

Do NOT use a separate file — keep everything in app.py to match the existing pattern.

Add these constants:

# ── Pipeline config ──────────────────────────────────────────────────────────
CHAINS = ["solana", "ethereum", "base", "bsc"]
MIN_LIQUIDITY_USD   = 100_000
MCAP_MIN            = 5_000_000
MCAP_MAX            = 50_000_000
TOKEN_AGE_MIN_HOURS = 24
TOKEN_AGE_MAX_HOURS = 168
MIN_BUYER_SELL_RATIO = 1.2
MIN_VOL_MCAP_RATIO  = 0.10
POLL_INTERVAL_SECS  = 300
PIPELINE_SCORE_THRESHOLD = 70
CANDIDATES_CSV      = "candidates.csv"

Then add a DexPair dataclass (use Python dataclasses, not a dict) with these fields:
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
pair_url: str  # e.g. https://dexscreener.com/solana/PAIR_ADDRESS

Add a property: buyer_sell_ratio -> float = txns_24h_buys / max(txns_24h_sells, 1)

Add a function fetch_dex_pairs(chain: str) -> list[DexPair]:
  Use httpx.Client(trust_env=False, timeout=30.0) — same pattern as make_anthropic_client()
  Call: GET https://api.dexscreener.com/latest/dex/tokens/{chain}
  Also call: GET https://api.dexscreener.com/latest/dex/search?q={chain}+meme
  Parse response["pairs"] array into DexPair objects
  Handle missing fields gracefully with .get() and defaults (0.0 for floats, 0 for ints)
  Return empty list on any exception — log to st.warning, don't crash

Add a function search_dex_pairs(query: str) -> list[DexPair]:
  Call: GET https://api.dexscreener.com/latest/dex/search?q={query}
  Same httpx pattern, same error handling
  Return up to 10 pairs sorted by liquidity_usd descending
```

---

## Prompt 2 — Pre-filter gate (6 hard checks, no AI cost)

```
In app.py, after the fetch_dex_pairs and search_dex_pairs functions, add a
pre-filter function. This runs BEFORE any AI call to eliminate tokens cheaply.

Add this function:

def pre_filter(pair: DexPair) -> tuple[bool, str]:
    """
    Returns (passed, rejection_reason).
    Checks gates in order — fail fast on cheapest checks first.
    """

    # Gate 1 — Liquidity
    if pair.liquidity_usd < MIN_LIQUIDITY_USD:
        return False, f"Liquidity ${pair.liquidity_usd:,.0f} below ${MIN_LIQUIDITY_USD:,.0f} min"

    # Gate 2 — Market cap range
    if not (MCAP_MIN <= pair.market_cap <= MCAP_MAX):
        return False, f"Mcap ${pair.market_cap:,.0f} outside $5M–$50M window"

    # Gate 3 — Token age (24h–168h)
    age_hours = (datetime.utcnow() - pair.created_at).total_seconds() / 3600
    if not (TOKEN_AGE_MIN_HOURS <= age_hours <= TOKEN_AGE_MAX_HOURS):
        return False, f"Token age {age_hours:.1f}h outside 24h–168h window"

    # Gate 4 — Buyer/seller ratio
    if pair.buyer_sell_ratio < MIN_BUYER_SELL_RATIO:
        return False, f"Buy/sell ratio {pair.buyer_sell_ratio:.2f} below {MIN_BUYER_SELL_RATIO} min"

    # Gate 5 — Momentum: at least 2 of 3 must be true
    momentum_checks = [
        pair.price_change_1h  > 5.0,
        pair.price_change_6h  > 10.0,
        pair.price_change_24h > 20.0,
    ]
    if sum(momentum_checks) < 2:
        return False, (
            f"Insufficient momentum — "
            f"1h={pair.price_change_1h:.1f}% "
            f"6h={pair.price_change_6h:.1f}% "
            f"24h={pair.price_change_24h:.1f}%"
        )

    # Gate 6 — Volume/mcap ratio
    vol_mcap = pair.volume_24h / max(pair.market_cap, 1)
    if vol_mcap < MIN_VOL_MCAP_RATIO:
        return False, f"Vol/mcap {vol_mcap:.1%} below {MIN_VOL_MCAP_RATIO:.0%} min"

    return True, ""

Do not modify any existing functions. Do not add Streamlit UI yet.
```

---

## Prompt 3 — Quant scorer (sections C and E1 from on-chain data)

```
In app.py, after the pre_filter function, add a quant_score function.
This computes sections C (25pts) and E1 (6pts) directly from DexPair data.
No AI call. Pure math. Returns a dict matching the scores/breakdown structure
already used in SYSTEM_PROMPT and result["scores"].

Add this function:

def quant_score(pair: DexPair) -> dict:
    """
    Scores sections C and E1 from DexScreener on-chain data.
    Returns: {
        "scores": {"C": float, "E_partial": float},
        "breakdown": {"C1": float, "C2": float, "C3": float, "E1": float},
        "evidence": {"C1": str, "C2": str, "C3": str, "E1": str}
    }
    E2 (organic influencer) always 0 here — requires AI judgment.
    """

    # C1 — Holder velocity proxy via buy transaction count (10pts)
    buys = pair.txns_24h_buys
    if   buys >= 500: c1 = 10.0
    elif buys >= 200: c1 = 7.0
    elif buys >= 100: c1 = 5.0
    elif buys >= 50:  c1 = 3.0
    else:             c1 = 0.0
    c1_evidence = f"Buy txns 24h: {buys}"

    # C2 — Volume/mcap ratio (8pts)
    ratio = pair.volume_24h / max(pair.market_cap, 1)
    if   ratio >= 0.30: c2 = 8.0
    elif ratio >= 0.15: c2 = 5.0
    elif ratio >= 0.10: c2 = 3.0
    else:               c2 = 0.0
    c2_evidence = f"Vol/mcap: {ratio:.1%}"

    # C3 — Buyer/seller ratio proxy (7pts)
    bsr = pair.buyer_sell_ratio
    if   bsr >= 2.0: c3 = 7.0
    elif bsr >= 1.5: c3 = 5.0
    elif bsr >= 1.2: c3 = 3.0
    else:            c3 = 0.0
    c3_evidence = f"Buy/sell ratio: {bsr:.2f}"

    # E1 — Price momentum cascade (6pts)
    m5  = pair.price_change_5m
    m1h = pair.price_change_1h
    m6h = pair.price_change_6h
    m24 = pair.price_change_24h
    if   m5 > 5  and m1h > 20:  e1 = 6.0
    elif m1h > 10 and m6h > 25: e1 = 5.0
    elif m1h > 5  and m24 > 20: e1 = 4.0
    elif m24 > 10:               e1 = 2.0
    else:                        e1 = 0.0
    e1_evidence = f"5m={m5:.1f}% 1h={m1h:.1f}% 6h={m6h:.1f}% 24h={m24:.1f}%"

    return {
        "scores":    {"C": c1 + c2 + c3, "E_partial": e1},
        "breakdown": {"C1": c1, "C2": c2, "C3": c3, "E1": e1},
        "evidence":  {"C1": c1_evidence, "C2": c2_evidence,
                      "C3": c3_evidence, "E1": e1_evidence},
    }
```

---

## Prompt 4 — Hybrid AI scorer (A, B, D, E2 only — C and E1 pre-filled)

```
In app.py, add a new constant HYBRID_SYSTEM_PROMPT directly below SYSTEM_PROMPT.
Do NOT modify SYSTEM_PROMPT — the existing Tab 2 analyser still uses it.
HYBRID_SYSTEM_PROMPT is used only by the pipeline flow.

HYBRID_SYSTEM_PROMPT = """You are the Memecoin Runner Indicator engine scoring
a token that has already passed on-chain pre-filters and has quantitative
scores pre-computed for sections C and E1.

YOU MUST ONLY SCORE:
- Section A (meme foundation, 25pts): A1(10) A2(8) A3(7)
- Section B (token structure, 25pts): B1(8) B2(7) B3(10)
- Section D (cycle and meta fit, 15pts): D1(7) D2(8)
- Section E2 ONLY (organic influencer pickup, 4pts)
- All 6 veto checks

DO NOT re-score C1, C2, C3, or E1 — they are provided from on-chain data.

[same framework criteria text as SYSTEM_PROMPT for A, B, D, E2, veto checks]

Respond ONLY with a valid JSON object:
{
  "scores": {"A": 0, "B": 0, "D": 0, "E2": 0},
  "breakdown": {"A1":0,"A2":0,"A3":0,"B1":0,"B2":0,"B3":0,"D1":0,"D2":0,"E2":0},
  "vetoFails": [],
  "findings": [{"icon": "+"|"~"|"x", "text": "..."}],
  "runnerSummary": "2–3 sentences",
  "confidence": "high|medium|low",
  "confidenceNote": "..."
}"""

Then add this function:

def score_coin_hybrid(pair: DexPair, quant: dict) -> dict | None:
    """
    Full hybrid scoring: quant (C+E1) + AI (A+B+D+E2+vetos).
    Returns a result dict in the same shape as existing result dicts
    (compatible with render_analyser_tab's display logic).
    Returns None on API error.
    """
    api_key = get_api_key()
    if not api_key:
        return None

    evidence_block = "\n".join(
        f"  {k}: {v}" for k, v in quant["evidence"].items()
    )
    user_msg = (
        f"Token: {pair.token_symbol} ({pair.token_name}) on {pair.chain_id}\n"
        f"Pair: {pair.pair_address}\n"
        f"Mcap: ${pair.market_cap:,.0f} | Liquidity: ${pair.liquidity_usd:,.0f}\n"
        f"Pre-computed on-chain scores:\n{evidence_block}\n\n"
        f"Score sections A, B, D, E2, and all veto checks."
    )

    try:
        client = make_anthropic_client(api_key)   # reuse existing function
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1000,
            system=HYBRID_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_msg}]
        )
        raw = message.content[0].text
        clean = re.sub(r"```json|```", "", raw).strip()
        ai = json.loads(clean)
    except Exception:
        return None

    # Merge quant + AI into unified result dict (same shape as Tab 2 results)
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
        # Identity — matches shape expected by render_analyser_tab
        "query":        pair.token_symbol,
        "name":         pair.token_name,
        "ticker":       pair.token_symbol,
        "chain":        pair.chain_id,
        "launched":     pair.created_at.strftime("%b %Y"),
        "currentMcap":  f"~${pair.market_cap/1e6:.1f}M",
        "athMcap":      "Unknown",
        "scores":       merged_scores,
        "breakdown":    {**quant["breakdown"], **ai.get("breakdown", {})},
        "vetoFails":    ai.get("vetoFails", []),
        "findings":     ai.get("findings", []),
        "runnerSummary":ai.get("runnerSummary", ""),
        "confidence":   ai.get("confidence", "medium"),
        "confidenceNote": ai.get("confidenceNote", ""),
        "total":        total,
        "vetoed":       vetoed,
        "timestamp":    datetime.now().strftime("%H:%M:%S"),
        # Pipeline-specific extras
        "pair_address": pair.pair_address,
        "pair_url":     pair.pair_url,
        "liquidity_usd":pair.liquidity_usd,
        "volume_24h":   pair.volume_24h,
        "vol_mcap_ratio": pair.volume_24h / max(pair.market_cap, 1),
        "buyer_sell_ratio": pair.buyer_sell_ratio,
        "price_change_1h":  pair.price_change_1h,
        "price_change_6h":  pair.price_change_6h,
        "price_change_24h": pair.price_change_24h,
        "scoring_method": "hybrid",
    }
```

---

## Prompt 5 — CSV logger

```
In app.py, after score_coin_hybrid, add two functions for CSV logging.

import csv   ← add to the imports block at the top of the file

CSV_COLUMNS = [
    "timestamp", "ticker", "name", "chain", "pair_address",
    "current_mcap", "liquidity_usd", "volume_24h", "vol_mcap_ratio",
    "buyer_sell_ratio", "price_change_1h", "price_change_6h", "price_change_24h",
    "score_total", "score_a", "score_b", "score_c", "score_d", "score_e",
    "vetoed", "veto_fails", "verdict", "runner_gap",
    "confidence", "runner_summary", "pair_url",
]

def log_candidate(result: dict) -> bool:
    """
    Append result to CANDIDATES_CSV. Deduplicates by (ticker, chain).
    Returns True if logged (new), False if skipped (duplicate).
    """
    exists = set()
    if os.path.exists(CANDIDATES_CSV):
        with open(CANDIDATES_CSV, newline="") as f:
            for row in csv.DictReader(f):
                exists.add((row["ticker"], row["chain"]))

    key = (result.get("ticker", ""), result.get("chain", ""))
    if key in exists:
        return False

    verdict_text, _ = get_verdict(result["total"], result["vetoed"])
    gap = result["total"] - AVG_BENCHMARK

    row = {
        "timestamp":       result.get("timestamp", ""),
        "ticker":          result.get("ticker", ""),
        "name":            result.get("name", ""),
        "chain":           result.get("chain", ""),
        "pair_address":    result.get("pair_address", ""),
        "current_mcap":    result.get("currentMcap", ""),
        "liquidity_usd":   f"{result.get('liquidity_usd', 0):,.0f}",
        "volume_24h":      f"{result.get('volume_24h', 0):,.0f}",
        "vol_mcap_ratio":  f"{result.get('vol_mcap_ratio', 0):.1%}",
        "buyer_sell_ratio":f"{result.get('buyer_sell_ratio', 0):.2f}",
        "price_change_1h": f"{result.get('price_change_1h', 0):.1f}%",
        "price_change_6h": f"{result.get('price_change_6h', 0):.1f}%",
        "price_change_24h":f"{result.get('price_change_24h', 0):.1f}%",
        "score_total":     result["total"],
        "score_a":         round(result["scores"].get("A", 0)),
        "score_b":         round(result["scores"].get("B", 0)),
        "score_c":         round(result["scores"].get("C", 0)),
        "score_d":         round(result["scores"].get("D", 0)),
        "score_e":         round(result["scores"].get("E", 0)),
        "vetoed":          result["vetoed"],
        "veto_fails":      "|".join(result.get("vetoFails", [])),
        "verdict":         verdict_text,
        "runner_gap":      f"{'+' if gap >= 0 else ''}{gap}",
        "confidence":      result.get("confidence", ""),
        "runner_summary":  result.get("runnerSummary", ""),
        "pair_url":        result.get("pair_url", ""),
    }

    write_header = not os.path.exists(CANDIDATES_CSV)
    with open(CANDIDATES_CSV, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        if write_header:
            writer.writeheader()
        writer.writerow(row)
    return True


def load_candidates(n: int = 100) -> list[dict]:
    """Load last n rows from CSV, newest first."""
    if not os.path.exists(CANDIDATES_CSV):
        return []
    with open(CANDIDATES_CSV, newline="") as f:
        rows = list(csv.DictReader(f))
    return list(reversed(rows[-n:]))
```

---

## Prompt 6 — Live feed tab (Tab 3)

```
In app.py, add a new function render_live_feed_tab() and wire it into main().

This function follows the same render_*_tab() pattern as render_methodology_tab()
and render_analyser_tab(). Do NOT modify those functions.

def render_live_feed_tab():
    st.markdown("## Live feed — pipeline candidates")
    st.markdown(
        "Tokens that passed all 6 pre-filter gates and scored ≥ 70 on the inversal framework. "
        "Run the pipeline from the sidebar to populate this feed."
    )

    # ── Controls row ────────────────────────────────────────────────────────
    ctrl1, ctrl2, ctrl3 = st.columns([2, 1, 1])
    with ctrl1:
        chain_filter = st.selectbox(
            "Chain", ["All", "solana", "ethereum", "base", "bsc"],
            label_visibility="collapsed"
        )
    with ctrl2:
        min_score = st.slider("Min score", 50, 100, PIPELINE_SCORE_THRESHOLD, step=5)
    with ctrl3:
        if st.button("Refresh ↻", use_container_width=True):
            st.rerun()

    # ── Load data ───────────────────────────────────────────────────────────
    rows = load_candidates(200)
    if chain_filter != "All":
        rows = [r for r in rows if r.get("chain") == chain_filter]
    rows = [r for r in rows if int(r.get("score_total", 0)) >= min_score]

    if not rows:
        st.info("No candidates yet. Run the pipeline from the sidebar to start scanning.")
        return

    # ── Summary metrics ─────────────────────────────────────────────────────
    m1, m2, m3, m4 = st.columns(4)
    scores = [int(r.get("score_total", 0)) for r in rows]
    strong = sum(1 for s in scores if s >= 85)
    avg_s  = sum(scores) / len(scores) if scores else 0
    chains = [r.get("chain","") for r in rows]
    top_chain = max(set(chains), key=chains.count) if chains else "—"
    m1.metric("Candidates", len(rows))
    m2.metric("Strong signal (≥85)", strong)
    m3.metric("Avg score", f"{avg_s:.0f}")
    m4.metric("Top chain", top_chain)

    st.markdown("---")

    # ── Candidate cards ──────────────────────────────────────────────────────
    for row in rows:
        score = int(row.get("score_total", 0))
        vetoed = row.get("vetoed", "False") == "True"
        verdict_text, verdict_class = get_verdict(score, vetoed)
        sc = score_color(score, vetoed)
        gap = score - AVG_BENCHMARK
        gap_str = f"+{gap}" if gap >= 0 else str(gap)

        with st.expander(
            f"**{row.get('ticker','?')}** · {row.get('chain','?')} · "
            f"Score: {score}/100 · {verdict_text} · Gap: {gap_str}",
            expanded=False
        ):
            c1, c2, c3 = st.columns([2, 2, 1])

            with c1:
                st.markdown(f"**{row.get('name','?')}** ({row.get('ticker','?')})")
                st.caption(f"{row.get('chain','?')} · Mcap {row.get('current_mcap','?')} · {row.get('timestamp','')}")
                st.markdown(
                    f"Liq: **${float(row.get('liquidity_usd','0').replace(',',''))/(1e3):.0f}K** · "
                    f"Vol/mcap: **{row.get('vol_mcap_ratio','?')}** · "
                    f"Buy/sell: **{row.get('buyer_sell_ratio','?')}** · "
                    f"1h: **{row.get('price_change_1h','?')}** · "
                    f"6h: **{row.get('price_change_6h','?')}**"
                )

            with c2:
                # Mini section bars — A B C D E
                section_vals = [
                    ("A", int(row.get("score_a", 0)), 25, "#6366f1"),
                    ("B", int(row.get("score_b", 0)), 25, "#10b981"),
                    ("C", int(row.get("score_c", 0)), 25, "#f59e0b"),
                    ("D", int(row.get("score_d", 0)), 15, "#ef4444"),
                    ("E", int(row.get("score_e", 0)), 10, "#ec4899"),
                ]
                for sid, val, smax, scolor in section_vals:
                    bc1, bc2 = st.columns([3, 1])
                    with bc1:
                        st.progress(val / smax)
                    with bc2:
                        st.caption(f"{sid} {val}")

            with c3:
                st.markdown(
                    f"<div style='font-size:2.5rem;font-weight:800;color:{sc};text-align:center;line-height:1'>{score}</div>"
                    f"<div style='text-align:center'><span class='verdict-pill {verdict_class}'>{verdict_text}</span></div>",
                    unsafe_allow_html=True
                )
                if row.get("pair_url"):
                    st.link_button("DexScreener ↗", row["pair_url"], use_container_width=True)
                if st.button("Re-analyse ↗", key=f"ra_{row.get('pair_address','')}", use_container_width=True):
                    st.session_state["prefill_query"] = row.get("ticker", "")
                    st.rerun()

            if row.get("runner_summary"):
                st.info(row["runner_summary"])

            if row.get("veto_fails"):
                st.error(f"Veto fails: {row['veto_fails']}")


In main(), update the tabs line to:

    tab1, tab2, tab3 = st.tabs([
        "📖 Methodology and framework",
        "🔍 Analyse a coin",
        "📡 Live feed"
    ])

    with tab1:
        render_methodology_tab()
    with tab2:
        render_analyser_tab()
    with tab3:
        render_live_feed_tab()

Also in render_analyser_tab(), after the `if "history" not in st.session_state:` block,
add this to pre-fill the search from the live feed Re-analyse button:

    if "prefill_query" in st.session_state:
        prefill = st.session_state.pop("prefill_query")
        # set the text_input default — handled via the query_to_run logic below
```

---

## Prompt 7 — Pipeline sidebar controls

```
In main(), inside the `with st.sidebar:` block, AFTER the existing API key section,
add pipeline controls. Keep the existing API key UI exactly as-is.

Add this after the API key block in the sidebar:

    st.markdown("---")
    st.markdown("### Pipeline")

    pipeline_mode = st.radio(
        "Mode",
        ["Off", "Poll (5 min)", "Stream (30s)", "Manual search"],
        help="Poll: scans all chains every 5 min. Stream: fast scans boosted pairs. Manual: search a specific token."
    )

    if pipeline_mode == "Manual search":
        manual_q = st.text_input("Token name or address", placeholder="e.g. BONK or 0x...")
        run_manual = st.button("Scan ↗", type="primary", use_container_width=True)
        if run_manual and manual_q.strip():
            with st.spinner(f"Scanning {manual_q}..."):
                pairs = search_dex_pairs(manual_q.strip())
                filtered = [(p, r) for p in pairs
                            if (r := pre_filter(p))[0]]
                for pair, _ in filtered[:5]:
                    quant = quant_score(pair)
                    result = score_coin_hybrid(pair, quant)
                    if result and result["total"] >= PIPELINE_SCORE_THRESHOLD:
                        logged = log_candidate(result)
                        st.sidebar.success(
                            f"{'Logged' if logged else 'Already logged'}: "
                            f"{pair.token_symbol} — {result['total']}/100"
                        )
                    elif result:
                        st.sidebar.info(
                            f"{pair.token_symbol} scored {result['total']}/100 — below threshold"
                        )
                if not filtered:
                    st.sidebar.warning(f"No pairs passed pre-filters for '{manual_q}'")

    elif pipeline_mode in ("Poll (5 min)", "Stream (30s)"):
        st.info(
            "Automated polling runs as a background process. "
            "Start it from the terminal:\n\n"
            "```\npython pipeline_runner.py\n```"
        )
        st.caption("The live feed tab updates as candidates are logged to candidates.csv")

    # Pipeline stats
    rows = load_candidates(1000)
    if rows:
        st.markdown("---")
        st.caption(f"**{len(rows)}** candidates logged · last: {rows[0].get('timestamp','')}")
```

---

## Prompt 8 — Background pipeline runner (separate file)

```
Create a new file pipeline_runner.py in the same folder as app.py.
This is a standalone script — NOT part of the Streamlit app.
It handles Poll and Stream modes without Streamlit's process model.

It should:
- Import DexPair, fetch_dex_pairs, pre_filter, quant_score, score_coin_hybrid,
  log_candidate, CHAINS, POLL_INTERVAL_SECS, PIPELINE_SCORE_THRESHOLD from app.py
- Use argparse for --mode [poll|stream] and --chains (comma-separated, default all)
- For poll mode: loop over CHAINS, call fetch_dex_pairs(chain), run pre_filter,
  quant_score, score_coin_hybrid, log_candidate for each passing pair,
  then sleep POLL_INTERVAL_SECS
- For stream mode: same but loop every 30 seconds with a seen_pairs set()
  to deduplicate by pair_address
- Print a one-line summary per pair: PASS/SKIP/LOGGED + ticker + score + reason
- Handle KeyboardInterrupt cleanly
- Load .env at top with: from dotenv import load_dotenv; load_dotenv()
- Use httpx.Client(trust_env=False) for all HTTP — same pattern as app.py

Usage:
  python pipeline_runner.py --mode poll
  python pipeline_runner.py --mode stream --chains solana,base

Also add pipeline_runner.py to README.md under a new "Pipeline" section.
```

---

## Prompt 9 — Final wiring check

```
Review app.py and pipeline_runner.py and fix any issues:

1. Verify all imports at the top of app.py include: os, csv, re, json,
   datetime, dataclasses, httpx, streamlit, anthropic, dotenv

2. Verify render_analyser_tab() handles the prefill_query session state:
   if st.session_state.get("prefill_query"):
       coin_query = st.session_state.pop("prefill_query")
   This should set the initial value for the text_input and trigger an analysis.

3. In render_live_feed_tab(), verify the float conversion for liquidity_usd
   handles both "100,000" (comma-formatted string) and "100000" (plain string).

4. Confirm pipeline_runner.py can import from app.py without triggering
   Streamlit code — add a guard: if __name__ != "__main__": skip st calls.
   Better approach: move the constants and non-Streamlit functions (DexPair,
   fetch_dex_pairs, search_dex_pairs, pre_filter, quant_score, score_coin_hybrid,
   log_candidate, load_candidates, CSV_COLUMNS, PIPELINE_* constants)
   into a new file pipeline.py and import from there in both app.py and
   pipeline_runner.py. Keep all Streamlit rendering functions in app.py only.

5. Add candidates.csv to .gitignore (create .gitignore if it doesn't exist).

6. Run the app to confirm no import errors:
   streamlit run app.py --server.headless true &
   sleep 3 && curl -s http://localhost:8501 | head -5
   Then kill the process.

7. Test the manual scan with a known token:
   python -c "
   from pipeline import search_dex_pairs, pre_filter, quant_score
   pairs = search_dex_pairs('BONK')
   print(f'Found {len(pairs)} pairs')
   if pairs:
       ok, reason = pre_filter(pairs[0])
       print(f'Filter: {ok} — {reason}')
       if ok:
           q = quant_score(pairs[0])
           print(f'Quant C={q[\"scores\"][\"C\"]} E1={q[\"scores\"][\"E_partial\"]}')
   "
```

---

## Order to send these prompts

1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9

Wait for Cursor to finish and confirm no errors before sending the next one.
Prompts 6 and 7 are the longest — give Cursor more time on those.
Prompt 9 is the integration check — send last, after everything else is in place.

## Key things Cursor needs to preserve

- `make_anthropic_client()` — never replace with plain `anthropic.Anthropic()`
- `get_api_key()` — single source of truth for the API key, used by hybrid scorer
- `httpx.Client(trust_env=False)` — required for both Anthropic and DexScreener calls
- `run.sh` — do not modify, it handles proxy clearing automatically
- `SYSTEM_PROMPT` — do not modify, Tab 2 still uses it unchanged
- `.env` loading at top — already there via `load_dotenv()`
- `AVG_BENCHMARK = 81` — used in runner gap calculation everywhere
