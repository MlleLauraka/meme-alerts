import os
import streamlit as st
import anthropic
import json
import re
import pandas as pd
from datetime import datetime, timezone
from dotenv import load_dotenv

from pipeline import (
    MCAP_MAX,
    MCAP_MIN,
    PIPELINE_SCORE_THRESHOLD,
    TOKEN_AGE_MAX_HOURS,
    TOKEN_AGE_MIN_HOURS,
    load_candidates,
    log_candidate,
    make_anthropic_client,
    parse_liquidity_usd,
    pre_filter,
    quant_score,
    score_coin_hybrid,
    search_dex_pairs,
)
from weekly_report import (
    TREND_LOOKBACK_DAYS,
    WEEKLY_REPORT_XLSX,
    compute_trends,
    get_report_meta,
    load_snapshots,
    run_weekly_scan,
)
from ath_data import ATH_DATA, VERDICT_ORDER

ATH_BATCHES = [
    "Top 100 3x><5x",
    "Top 100 >5x",
    "2x +potential ATH",
]

BATCH_LEGACY_ALIASES = {
    "Major Alts": "Top 100 3x><5x",
    "L1s & DeFi": "Top 100 >5x",
    "2x ATH": "2x +potential ATH",
    "Meme Coins": None,
}


def normalize_batch_filter(value):
    if not value or value == "All":
        return "All"
    if value in BATCH_LEGACY_ALIASES:
        mapped = BATCH_LEGACY_ALIASES[value]
        return mapped if mapped else "All"
    if value in ATH_BATCHES:
        return value
    return "All"

load_dotenv()

st.set_page_config(
    page_title="Memecoin Runner Indicator",
    page_icon="🪙",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
    .main .block-container {
        padding-top: 2rem;
        max-width: 1100px;
        padding-left: max(1rem, env(safe-area-inset-left));
        padding-right: max(1rem, env(safe-area-inset-right));
        padding-bottom: max(1rem, env(safe-area-inset-bottom));
    }
    .metric-card {
        background: #f8f9fa;
        border: 1px solid #e9ecef;
        border-radius: 10px;
        padding: 1rem 1.25rem;
        text-align: center;
    }
    .score-big {
        font-size: 3rem;
        font-weight: 700;
        line-height: 1;
    }
    .verdict-pill {
        display: inline-block;
        padding: 4px 14px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .strong-signal { background: #d1fae5; color: #065f46; }
    .promising    { background: #dcfce7; color: #166534; }
    .speculative  { background: #fef3c7; color: #92400e; }
    .do-not       { background: #fee2e2; color: #991b1b; }
    .disqualified { background: #fee2e2; color: #991b1b; }
    .veto-box {
        background: #fee2e2;
        border: 1px solid #fca5a5;
        border-radius: 8px;
        padding: 0.75rem 1rem;
        margin-top: 0.5rem;
        font-size: 0.85rem;
        color: #991b1b;
        font-weight: 600;
    }
    .finding-pos { color: #16a34a; font-weight: 600; }
    .finding-neu { color: #d97706; font-weight: 600; }
    .finding-neg { color: #dc2626; font-weight: 600; }
    .bench-row {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        padding: 0.4rem 0;
        border-bottom: 1px solid #f1f5f9;
        font-size: 0.85rem;
    }
    .gap-positive { background: #d1fae5; color: #065f46; border-radius: 8px; padding: 0.6rem 1rem; font-weight: 600; }
    .gap-neutral  { background: #fef3c7; color: #92400e; border-radius: 8px; padding: 0.6rem 1rem; font-weight: 600; }
    .gap-negative { background: #fee2e2; color: #991b1b; border-radius: 8px; padding: 0.6rem 1rem; font-weight: 600; }
    .criterion-row {
        background: #f8fafc;
        border-radius: 8px;
        padding: 0.75rem 1rem;
        margin-bottom: 0.5rem;
        border-left: 3px solid #6366f1;
    }
    .veto-pass { color: #16a34a; font-weight: 600; }
    .veto-fail { color: #dc2626; font-weight: 600; }
    .history-item {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 0.75rem 1rem;
        margin-bottom: 0.5rem;
        cursor: pointer;
    }
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #6366f1, #8b5cf6);
    }
    .section-header {
        font-size: 0.7rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #94a3b8;
        margin-bottom: 0.5rem;
        margin-top: 1.5rem;
    }
    .ath-list {
        display: grid;
        gap: 0.65rem;
        margin-top: 0.5rem;
    }
    .ath-card {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 0.85rem 1rem;
    }
    .ath-card-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 0.5rem;
        flex-wrap: wrap;
        margin-bottom: 0.25rem;
    }
    .ath-ticker {
        font-weight: 700;
        color: #1e293b;
        font-size: 0.95rem;
    }
    .ath-badge {
        font-size: 0.68rem;
        font-weight: 600;
        padding: 3px 8px;
        border-radius: 10px;
        white-space: nowrap;
    }
    .ath-name {
        color: #475569;
        font-size: 0.82rem;
        margin-bottom: 0.6rem;
    }
    .ath-stats {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 0.5rem;
        margin: 0 0 0.6rem 0;
    }
    .ath-stats > div {
        background: #fff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 0.45rem 0.55rem;
    }
    .ath-stats dt {
        font-size: 0.62rem;
        font-weight: 700;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        color: #94a3b8;
        margin: 0;
    }
    .ath-stats dd {
        margin: 0.15rem 0 0 0;
        font-size: 0.8rem;
        font-weight: 600;
        color: #1e293b;
        word-break: break-word;
    }
    .ath-notes {
        margin: 0;
        color: #64748b;
        font-size: 0.78rem;
        line-height: 1.45;
    }
    .quick-picks-label {
        margin-top: 0.5rem;
        margin-bottom: 0.25rem;
        font-size: 0.75rem;
        color: #94a3b8;
    }
    @media (max-width: 480px) {
        .main .block-container {
            padding-top: max(0.75rem, env(safe-area-inset-top));
            padding-left: max(0.75rem, env(safe-area-inset-left));
            padding-right: max(0.75rem, env(safe-area-inset-right));
        }
        h1 { font-size: 1.45rem !important; line-height: 1.25 !important; }
        h2 { font-size: 1.2rem !important; line-height: 1.3 !important; }
        h3, h4 { font-size: 1rem !important; }
        .score-big { font-size: 2rem !important; }
        .score-hero { font-size: 2rem !important; }
        [data-testid="stHorizontalBlock"] {
            flex-wrap: wrap !important;
            gap: 0.35rem !important;
        }
        [data-testid="column"] {
            flex: 1 1 100% !important;
            width: 100% !important;
            min-width: 0 !important;
        }
        [data-testid="stTabs"] [data-baseweb="tab-list"] {
            flex-wrap: nowrap !important;
            overflow-x: auto !important;
            -webkit-overflow-scrolling: touch;
            scrollbar-width: none;
        }
        [data-testid="stTabs"] [data-baseweb="tab-list"]::-webkit-scrollbar {
            display: none;
        }
        [data-testid="stTabs"] button[data-baseweb="tab"] {
            white-space: nowrap;
            font-size: 0.78rem;
            min-height: 44px;
            padding: 0.35rem 0.65rem;
        }
        .stButton > button {
            min-height: 44px;
            font-size: 0.9rem;
        }
        .stTextInput input, .stSelectbox div, .stMultiSelect div {
            min-height: 44px;
            font-size: 16px !important;
        }
        div[data-testid="stDataFrame"], div[data-testid="stDataFrame"] > div {
            overflow-x: auto !important;
            -webkit-overflow-scrolling: touch;
        }
        .ath-stats {
            grid-template-columns: 1fr 1fr;
        }
        .ath-stats > div:last-child:nth-child(odd) {
            grid-column: 1 / -1;
        }
        .verdict-pill { font-size: 0.72rem; }
        .gap-positive, .gap-neutral, .gap-negative {
            font-size: 0.85rem;
            padding: 0.55rem 0.75rem;
        }
    }
    @media (min-width: 768px) {
        .ath-list { grid-template-columns: 1fr 1fr; }
    }
    @media (min-width: 481px) and (max-width: 767px) {
        [data-testid="stHorizontalBlock"]:has(> [data-testid="column"]:nth-child(5)) [data-testid="column"] {
            flex: 1 1 calc(50% - 0.5rem) !important;
            min-width: calc(50% - 0.5rem) !important;
        }
    }
</style>
""", unsafe_allow_html=True)

BENCHMARKS = [
    {"name": "PEPE",   "score": 91, "peak": "~$8B",   "chain": "ETH", "launched": "Apr 2023"},
    {"name": "PNUT",   "score": 90, "peak": "~$2B",   "chain": "SOL", "launched": "Oct 2024"},
    {"name": "WIF",    "score": 86, "peak": "~$5B",   "chain": "SOL", "launched": "Nov 2023"},
    {"name": "GOAT",   "score": 85, "peak": "~$1.5B", "chain": "SOL", "launched": "Oct 2024"},
    {"name": "POPCAT", "score": 85, "peak": "~$2B",   "chain": "SOL", "launched": "Dec 2023"},
    {"name": "BOME",   "score": 74, "peak": "~$1.5B", "chain": "SOL", "launched": "Mar 2024"},
]
AVG_BENCHMARK = 81
FLOOR_BENCHMARK = 74

SYSTEM_PROMPT = """You are the Memecoin Runner Indicator engine. You have deep knowledge of the Inversal Framework for identifying potential $1B+ memecoin candidates.

The framework scores coins across 5 sections (total 100pts):
A · Meme foundation (25pts max): A1=pre-existing meme recognition(10), A2=emotional charge(8), A3=remixability(7)
B · Token structure (25pts max): B1=LP burned/locked(8), B2=contract renounced(7), B3=supply distribution(10)
C · Organic growth (25pts max): C1=holder velocity(10), C2=volume/mcap ratio(8), C3=community spontaneity(7)
D · Cycle and meta fit (15pts max): D1=BTC halving proximity(7), D2=archetype novelty(8)
E · Launch velocity (10pts max): E1=72hr price action(6), E2=organic influencer pickup(4)

Veto checks (any fail = disqualify regardless of score):
V1: LP burned or locked, V2: zero buy/sell tax, V3: no presale/VC allocation, V4: no utility/roadmap promised, V5: team wallet under 10% of supply, V6: meme predates the token

Benchmark cohort (verified $1B+ coins, avg=81): PEPE=91, PNUT=90, WIF=86, GOAT=85, POPCAT=85, BOME=74
TRUMP was disqualified (80% insider supply, 3-year vesting) despite $27B peak — outlier excluded from avg.

The current date is June 2026. Bitcoin's last halving was April 2024. We are ~26 months post-halving — a subdued phase for memes. Next halving ~April 2028.

Respond ONLY with a valid JSON object. No preamble, no markdown fences, no explanation outside the JSON:
{
  "name": "full coin name",
  "ticker": "TICKER",
  "chain": "chain name",
  "launched": "approximate launch date or Unknown",
  "currentMcap": "approximate current market cap e.g. ~$150M or Unknown",
  "athMcap": "approximate ATH market cap or Unknown",
  "scores": {"A": 0, "B": 0, "C": 0, "D": 0, "E": 0},
  "breakdown": {"A1":0,"A2":0,"A3":0,"B1":0,"B2":0,"B3":0,"C1":0,"C2":0,"C3":0,"D1":0,"D2":0,"E1":0,"E2":0},
  "vetoFails": ["V1","V3"],
  "findings": [
    {"icon": "+", "text": "positive finding"},
    {"icon": "~", "text": "neutral or mixed finding"},
    {"icon": "x", "text": "negative finding"}
  ],
  "runnerSummary": "2-3 sentence summary of whether the structural profile matches the $1B cohort and the single biggest factor holding it back or pushing it forward",
  "confidence": "high|medium|low",
  "confidenceNote": "brief note on data availability"
}"""

def get_verdict(total, vetoed):
    if vetoed: return "Disqualified", "disqualified"
    if total >= 85: return "Strong signal", "strong-signal"
    if total >= 70: return "Promising", "promising"
    if total >= 50: return "Speculative", "speculative"
    return "Do not proceed", "do-not"

def get_gap_class(gap, vetoed):
    if vetoed: return "gap-negative"
    if gap >= 0: return "gap-positive"
    if gap >= -7: return "gap-neutral"
    return "gap-negative"

def score_color(total, vetoed):
    if vetoed: return "#dc2626"
    if total >= 85: return "#065f46"
    if total >= 70: return "#166534"
    if total >= 50: return "#92400e"
    return "#dc2626"

def render_methodology_tab():
    st.markdown("## Inversal framework — methodology and scoring guide")
    st.markdown("""
    The **Inversal Method** works top-down: instead of asking *"what makes a good memecoin?"*,
    it asks *"what did every confirmed \\$1B+ memecoin share before anyone knew it would succeed?"*
    Those shared attributes become the filter. The result is a set of **necessary conditions**
    — the floor below which no memecoin has reliably made it — not a prediction engine.
    """)

    st.info("💡 **Key insight:** The framework is almost entirely a set of elimination tests, not positive predictions. You can rule out ~99% of new launches in under 60 seconds using just sections A and B.")

    st.markdown("---")

    st.markdown("### The five scoring sections")

    sections = [
        {
            "id": "A", "name": "Meme foundation", "max": 25, "color": "#6366f1",
            "desc": "The underlying meme must exist and circulate independently of the token. No confirmed $1B memecoin invented its meme — they all tokenised something that was already alive.",
            "criteria": [
                ("A1", "Pre-existing meme recognition", 10, "Does the meme exist and circulate independently? Explainable in one sentence to a non-crypto person?\n\n0 = none · 4 = weak · 7 = known · 10 = viral globally"),
                ("A2", "Emotional charge", 8, "Does it trigger a clear, strong emotion — humor, outrage, nostalgia, tribal loyalty? Neutral memes rarely sustain momentum.\n\n0 = flat · 3 = mild · 5 = clear · 8 = strong"),
                ("A3", "Remixability", 7, "Can others spontaneously create derivative memes? The meme should be a template, not a finished joke.\n\n0 = rigid · 2 = limited · 5 = flexible · 7 = template"),
            ]
        },
        {
            "id": "B", "name": "Token structure", "max": 25, "color": "#10b981",
            "desc": "Every $1B memecoin in the benchmark set had a clean, verifiable token structure checkable on-chain in 60 seconds. No exceptions.",
            "criteria": [
                ("B1", "LP burned or time-locked", 8, "Liquidity pool tokens sent to dead address or locked via verifiable time-lock. Without this, the deployer can drain liquidity instantly.\n\n0 = none · 0 = locked short · 4 = locked long · 8 = burned"),
                ("B2", "Contract renounced", 7, "Owner set to 0x000... — no one can mint, pause, or change fees. Verifiable in seconds on Solscan / Etherscan.\n\n0 = not renounced · 7 = renounced"),
                ("B3", "Supply distribution", 10, "Top 10 wallets hold less than 20% of supply. No single wallet above 5%. No hidden team reserve in deployer.\n\n0 = concentrated · 3 = risky · 6 = ok · 10 = ideal"),
            ]
        },
        {
            "id": "C", "name": "Organic growth", "max": 25, "color": "#f59e0b",
            "desc": "The hardest signals to fake because wallets cost gas and community engagement costs time. These are measurable before any CEX listing.",
            "criteria": [
                ("C1", "Holder count velocity", 10, "Unique wallets growing 5–20%/day in first week without a Binance/Coinbase listing.\n\n0 = flat · 3 = <2%/day · 6 = 2–5%/day · 10 = 5%+/day"),
                ("C2", "Volume / mcap ratio", 8, "24h trading volume as % of market cap. >10% signals genuine turnover. >30% in early days is exceptional. Watch for wash-trading signs.\n\n0 = <2% · 2 = 2–5% · 5 = 5–15% · 8 = 15%+"),
                ("C3", "Community spontaneity", 7, "Meme remixes, X posts, and Telegram groups forming without a paid 'marketing wallet'.\n\n0 = paid shills · 2 = mixed · 5 = mostly organic · 7 = fully organic"),
            ]
        },
        {
            "id": "D", "name": "Cycle and meta fit", "max": 15, "color": "#ef4444",
            "desc": "Timing within the Bitcoin halving cycle is the single biggest variable that cannot be overcome by a high score elsewhere. Even perfect coins underperform in bear cycles.",
            "criteria": [
                ("D1", "Bitcoin halving proximity", 7, "Within 18 months post-halving is peak window. Halvings: Nov 2012, Jul 2016, May 2020, Apr 2024, ~Apr 2028. Current date: Jun 2026 = 26mo post-halving (subdued phase).\n\n0 = bear · 2 = pre-halving · 5 = 0–6mo post · 7 = 6–18mo post"),
                ("D2", "Archetype novelty", 8, "If DOGE is at $20B, another dog coin faces a ceiling. The $1B+ winners introduced a new archetype: first frog (PEPE), first cat on Solana (MEW), first AI meme (GOAT), first political coin (TRUMP).\n\n0 = saturated · 2 = crowded · 5 = fresh · 8 = first of kind"),
            ]
        },
        {
            "id": "E", "name": "Launch velocity", "max": 10, "color": "#ec4899",
            "desc": "The spark — it's there or it isn't. This is a confirmation filter, not a prediction. You can't pre-screen for it; you have to be watching at launch.",
            "criteria": [
                ("E1", "72-hour price action", 6, "Did the coin 10x+ in its first 72 hours with volume holding (not dumping immediately)?\n\n0 = flat · 2 = 2–5x · 4 = 5–10x · 6 = 10x+"),
                ("E2", "Organic influencer pickup", 4, "Known figure mentioning unpaid. Elon + DOGE. Marc Andreessen + GOAT. One genuine organic mention > 100 paid.\n\n0 = none · 0 = micro · 2 = mid · 4 = major organic"),
            ]
        },
    ]

    for sec in sections:
        with st.expander(f"**Section {sec['id']} · {sec['name']}** — {sec['max']} pts max", expanded=False):
            st.markdown(f"<div style='color:#64748b; margin-bottom:1rem'>{sec['desc']}</div>", unsafe_allow_html=True)
            for cid, cname, cmax, cdesc in sec["criteria"]:
                st.markdown(f"""
                <div class='criterion-row' style='border-left-color:{sec["color"]}'>
                    <strong>{cid} · {cname}</strong> <span style='color:#94a3b8; font-size:0.8rem'>({cmax} pts max)</span><br>
                    <span style='color:#64748b; font-size:0.85rem; white-space:pre-line'>{cdesc}</span>
                </div>
                """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### Veto checks — any fail = disqualified")
    st.markdown("These are non-negotiable hard stops derived from the $1B cohort. Every confirmed $1B memecoin passed all six. A coin can score 95/100 and still be disqualified if any veto fails.")

    vetos = [
        ("V1", "LP burned or locked", "Liquidity pool tokens permanently burned or verifiably locked. No burn/lock = deployer can drain at any time."),
        ("V2", "Zero buy/sell tax", "Any transaction tax above 0% is a mechanism to extract value from holders. Every $1B memecoin has zero taxes."),
        ("V3", "No presale or VC allocation", "Any form of pre-launch fundraising or VC deal. Fair launch only — BOME's quasi-presale nearly failed this check."),
        ("V4", "No utility or roadmap promised", "Every $1B memecoin explicitly refused to promise utility. Any whitepaper, roadmap, or governance mechanism is a red flag."),
        ("V5", "Team wallet under 10% of supply", "Any single insider address holding >10% of total supply. TRUMP's 80% insider supply is the extreme example."),
        ("V6", "Meme predates the token", "The cultural meme must exist independently before the token. Coins that invent their meme at launch have no cultural runway."),
    ]

    vcol1, vcol2 = st.columns(2)
    for i, (vid, vname, vdesc) in enumerate(vetos):
        col = vcol1 if i % 2 == 0 else vcol2
        with col:
            st.markdown(f"""
            <div style='background:#fef2f2; border:1px solid #fecaca; border-radius:8px; padding:0.75rem 1rem; margin-bottom:0.5rem; border-left:3px solid #ef4444'>
                <strong style='color:#991b1b'>{vid} · {vname}</strong><br>
                <span style='color:#64748b; font-size:0.82rem'>{vdesc}</span>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### Verdict thresholds and runner indicator")

    vcol1, vcol2, vcol3, vcol4, vcol5 = st.columns(5)
    thresholds = [
        ("85–100", "Strong signal", "#d1fae5", "#065f46", "Matches $1B cohort profile. All tiers passing."),
        ("70–84",  "Promising",     "#dcfce7", "#166534", "Most criteria met. Warrants close watching."),
        ("50–69",  "Speculative",   "#fef3c7", "#92400e", "Some signals present but significant gaps."),
        ("0–49",   "Do not proceed","#fee2e2", "#991b1b", "Does not meet baseline criteria."),
        ("Any veto", "Disqualified","#fee2e2", "#991b1b", "Hard stop. Non-negotiable structural flaw."),
    ]
    for col, (score, label, bg, fg, desc) in zip([vcol1,vcol2,vcol3,vcol4,vcol5], thresholds):
        with col:
            st.markdown(f"""
            <div style='background:{bg}; border-radius:10px; padding:1rem; text-align:center; height:130px'>
                <div style='font-size:0.75rem; color:{fg}; font-weight:700; margin-bottom:0.25rem'>{score}</div>
                <div style='font-size:0.9rem; font-weight:700; color:{fg}; margin-bottom:0.5rem'>{label}</div>
                <div style='font-size:0.72rem; color:{fg}; opacity:0.8'>{desc}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### Verified $1B+ benchmark cohort")
    st.markdown("These are the coins the framework was derived from — all confirmed to have reached $1B+ market cap. Scores are research-verified, not estimated.")

    bcols = st.columns(len(BENCHMARKS))
    for col, b in zip(bcols, BENCHMARKS):
        with col:
            score_pct = b["score"]
            color = "#065f46" if b["score"] >= 85 else "#166534" if b["score"] >= 70 else "#92400e"
            st.markdown(f"""
            <div style='background:#f8fafc; border:1px solid #e2e8f0; border-radius:10px; padding:0.75rem; text-align:center'>
                <div style='font-size:1rem; font-weight:700; color:#1e293b'>{b["name"]}</div>
                <div style='font-size:1.8rem; font-weight:700; color:{color}; line-height:1.1'>{b["score"]}</div>
                <div style='font-size:0.7rem; color:#94a3b8'>peak {b["peak"]}</div>
                <div style='font-size:0.7rem; color:#94a3b8'>{b["chain"]} · {b["launched"]}</div>
            </div>
            """, unsafe_allow_html=True)
            st.progress(b["score"] / 100)

    st.markdown(f"""
    <div style='background:#eff6ff; border:1px solid #bfdbfe; border-radius:8px; padding:0.75rem 1rem; margin-top:1rem; font-size:0.85rem; color:#1e40af'>
        <strong>Cohort avg: {AVG_BENCHMARK}/100</strong> · Floor: {FLOOR_BENCHMARK}/100 · 
        Gap formula: Candidate score − {AVG_BENCHMARK}.
        Positive gap = above cohort profile. Gap > −7 = within historical range of confirmed $1B achievers.
        <br><em>TRUMP excluded: disqualified (80% insider supply, 3yr vesting) despite $27B peak — unrepeatable presidential outlier.</em>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### Important caveats")
    cav1, cav2, cav3 = st.columns(3)
    with cav1:
        st.warning("**Necessary, not sufficient**\n\nPassing the threshold means structural similarity to past winners — not a prediction that the coin will reach $1B. Most coins that pass all criteria still never make it.")
    with cav2:
        st.warning("**Pure memecoins only**\n\nThe framework was derived from pure memecoins. AI infrastructure tokens, NFT projects with utility, and governance tokens fall outside its scope and should be evaluated differently.")
    with cav3:
        st.warning("**Cycle timing matters most**\n\nAs of June 2026 (~26 months post-halving), we are in a subdued phase for meme speculation. Even perfect structural scores face a cycle headwind until ~Apr 2028.")

def get_api_key():
    try:
        return st.secrets["ANTHROPIC_API_KEY"]
    except (KeyError, FileError, AttributeError):
        pass
    return os.environ.get("ANTHROPIC_API_KEY")

def format_api_error(exc):
    cause = exc.__cause__
    detail = str(cause or exc)
    if "403" in detail and "proxy" in detail.lower():
        return (
            "Network blocked by a local proxy. Run the app from macOS Terminal with "
            "`./run.sh`, or unset HTTP_PROXY/HTTPS_PROXY and restart."
        )
    if "nodename nor servname" in detail.lower() or "name or service not known" in detail.lower():
        return "Could not reach api.anthropic.com. Check your internet connection and DNS."
    return f"Could not reach Anthropic API: {detail}"

def summarize_pre_filter(pairs):
    """Per-pair pre-filter pass/fail details for the manual scan UI."""
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

def render_analyser_tab():
    st.markdown("## Coin analyser — run the runner indicator")

    st.markdown("""
    Enter any memecoin ticker or name. The AI will research it, score it against all five framework
    sections, check the six veto criteria, and calculate the **runner gap** vs the \\$1B benchmark cohort (avg = 81).
    """)

    api_key = get_api_key()
    if not api_key:
        st.warning("Coin analysis is unavailable — the server API key is not configured.")

    if "history" not in st.session_state:
        st.session_state.history = []
    if "current_result" not in st.session_state:
        st.session_state.current_result = None

    prefill_query = st.session_state.pop("prefill_query", None)
    if prefill_query:
        st.session_state.coin_query_input = prefill_query

    col_input, col_btn = st.columns([3, 1])
    with col_input:
        coin_query = st.text_input(
            "Coin name or ticker",
            placeholder="e.g. BONK, MOODENG, SHIB, FLOKI...",
            label_visibility="collapsed",
            key="coin_query_input",
        )
    with col_btn:
        analyse_clicked = st.button("Analyse ↗", type="primary", use_container_width=True)

    st.markdown("<div class='quick-picks-label'>Quick picks:</div>", unsafe_allow_html=True)
    quick_coins = ["BONK", "SHIB", "FLOKI", "MOODENG", "NEIRO", "MEW", "TURBO", "BABYDOGE", "BRETT", "MOG"]
    quick_selected = None
    for row_start in range(0, len(quick_coins), 5):
        qcols = st.columns(5)
        for col, qc in zip(qcols, quick_coins[row_start:row_start + 5]):
            with col:
                if st.button(qc, key=f"q_{qc}", use_container_width=True):
                    quick_selected = qc

    query_to_run = quick_selected or (coin_query if analyse_clicked else None)
    if prefill_query and not query_to_run:
        query_to_run = prefill_query

    if query_to_run:
        if not api_key:
            st.error("Analysis is unavailable — the server API key is not configured.")
            return
        with st.spinner(f"Researching {query_to_run.upper()} and scoring against the framework..."):
            try:
                client = make_anthropic_client(api_key)
                message = client.messages.create(
                    model="claude-sonnet-4-6",
                    max_tokens=1500,
                    system=SYSTEM_PROMPT,
                    messages=[{
                        "role": "user",
                        "content": f"Score this memecoin against the Inversal Framework: {query_to_run}. Use your best available knowledge. If data is limited, estimate conservatively and note confidence level."
                    }]
                )
                raw = message.content[0].text
                clean = re.sub(r"```json|```", "", raw).strip()
                result = json.loads(clean)

                total = round(sum(result["scores"].values()))
                vetoed = len(result.get("vetoFails", [])) > 0
                result["total"] = total
                result["vetoed"] = vetoed
                result["query"] = query_to_run
                result["timestamp"] = datetime.now().strftime("%H:%M:%S")

                st.session_state.current_result = result
                st.session_state.history.insert(0, result)

            except json.JSONDecodeError:
                st.error("The AI returned an unexpected format. Try again or try a different coin.")
                return
            except anthropic.AuthenticationError:
                st.error("Invalid API key on the server. Update `.env` locally or Streamlit secrets when deployed.")
                return
            except anthropic.APIConnectionError as e:
                st.error(format_api_error(e))
                return
            except anthropic.APIStatusError as e:
                st.error(f"Anthropic API error ({e.status_code}): {e.message}")
                return
            except Exception as e:
                st.error(f"Error: {e}")
                return

    if st.session_state.history:
        with st.sidebar:
            st.markdown("### Search history")
            for i, h in enumerate(st.session_state.history[:15]):
                verdict_text, _ = get_verdict(h["total"], h["vetoed"])
                score_display = "DQ" if h["vetoed"] else str(h["total"])
                if st.button(
                    f"{h.get('ticker', h['query'])} — {score_display} — {verdict_text}",
                    key=f"hist_{i}",
                    use_container_width=True
                ):
                    st.session_state.current_result = h

    result = st.session_state.current_result
    if not result:
        st.markdown("---")
        st.markdown("#### Benchmark reference")
        bcols = st.columns(len(BENCHMARKS))
        for col, b in zip(bcols, BENCHMARKS):
            with col:
                c = "#065f46" if b["score"] >= 85 else "#166534" if b["score"] >= 70 else "#92400e"
                st.markdown(f"""
                <div style='background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;padding:0.6rem;text-align:center'>
                    <div style='font-weight:700;color:#1e293b'>{b["name"]}</div>
                    <div style='font-size:1.5rem;font-weight:700;color:{c}'>{b["score"]}</div>
                    <div style='font-size:0.68rem;color:#94a3b8'>{b["peak"]} · {b["chain"]}</div>
                </div>
                """, unsafe_allow_html=True)
        return

    total = result["total"]
    vetoed = result["vetoed"]
    verdict_text, verdict_class = get_verdict(total, vetoed)
    gap = total - AVG_BENCHMARK
    gap_class = get_gap_class(gap, vetoed)
    sc = score_color(total, vetoed)

    st.markdown("---")

    r1c1, r1c2, r1c3 = st.columns([2, 1, 2])

    with r1c1:
        st.markdown(f"### {result.get('name', result['query'])} ({result.get('ticker', '?')})")
        st.markdown(f"""
        <div style='color:#64748b; font-size:0.85rem; margin-top:-0.5rem'>
            {result.get('chain','?')} · Launched {result.get('launched','?')} ·
            Mcap {result.get('currentMcap','?')} · ATH {result.get('athMcap','?')}
        </div>
        """, unsafe_allow_html=True)
        conf = result.get("confidence", "medium")
        conf_color = {"high": "#16a34a", "medium": "#d97706", "low": "#dc2626"}.get(conf, "#d97706")
        st.markdown(f"<span style='font-size:0.78rem; color:{conf_color}; font-weight:600'>Confidence: {conf.upper()}</span> — <span style='font-size:0.78rem; color:#94a3b8'>{result.get('confidenceNote','')}</span>", unsafe_allow_html=True)

    with r1c2:
        score_display = "DQ" if vetoed else str(total)
        st.markdown(f"""
        <div style='text-align:center; padding:1rem; background:#f8fafc; border-radius:12px; border:1px solid #e2e8f0'>
            <div class='score-big score-hero' style='font-weight:800; color:{sc}; line-height:1'>{score_display}</div>
            <div style='font-size:0.75rem; color:#94a3b8; margin-bottom:0.5rem'>/ 100</div>
            <span class='verdict-pill {verdict_class}'>{verdict_text}</span>
        </div>
        """, unsafe_allow_html=True)

    with r1c3:
        gap_sign = "+" if gap >= 0 else ""
        gap_display = "N/A (vetoed)" if vetoed else f"{gap_sign}{gap} pts"
        st.markdown(f"""
        <div class='{gap_class}' style='margin-bottom:0.75rem'>
            Runner gap vs \\$1B avg ({AVG_BENCHMARK}): <strong>{gap_display}</strong>
        </div>
        """, unsafe_allow_html=True)
        if vetoed:
            veto_list = ", ".join(result.get("vetoFails", []))
            st.markdown(f"""<div class='veto-box'>Veto fail(s): {veto_list} — disqualified regardless of score</div>""", unsafe_allow_html=True)
        else:
            if gap >= 0:
                st.success(f"Above threshold — structurally matches $1B cohort")
            elif gap >= -7:
                st.warning(f"Within historical range of confirmed $1B coins (floor: {FLOOR_BENCHMARK})")
            else:
                st.error(f"Below threshold — structural gap to close before $1B likely")

    st.markdown("---")

    left_col, right_col = st.columns([3, 2])

    with left_col:
        st.markdown("#### Section scores")

        sections_meta = [
            ("A", "Meme foundation", 25, "#6366f1"),
            ("B", "Token structure",  25, "#10b981"),
            ("C", "Organic growth",   25, "#f59e0b"),
            ("D", "Cycle fit",        15, "#ef4444"),
            ("E", "Launch velocity",  10, "#ec4899"),
        ]
        for sid, sname, smax, scolor in sections_meta:
            val = round(result["scores"].get(sid, 0))
            pct = val / smax
            sc2, sc3 = st.columns([3, 1])
            with sc2:
                st.markdown(f"<span style='font-size:0.82rem; color:#475569'><strong>{sid}</strong> · {sname}</span>", unsafe_allow_html=True)
                st.progress(pct)
            with sc3:
                st.markdown(f"<div style='text-align:right; padding-top:1.5rem; font-size:0.85rem; font-weight:700; color:#1e293b'>{val}/{smax}</div>", unsafe_allow_html=True)

        st.markdown("#### Key findings")
        for f in result.get("findings", []):
            icon = f["icon"]
            if icon == "+":
                st.markdown(f"<div style='padding:0.4rem 0'><span class='finding-pos'>+</span> <span style='font-size:0.85rem'>{f['text']}</span></div>", unsafe_allow_html=True)
            elif icon == "x":
                st.markdown(f"<div style='padding:0.4rem 0'><span class='finding-neg'>×</span> <span style='font-size:0.85rem'>{f['text']}</span></div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div style='padding:0.4rem 0'><span class='finding-neu'>~</span> <span style='font-size:0.85rem'>{f['text']}</span></div>", unsafe_allow_html=True)

    with right_col:
        st.markdown("#### Veto checks")
        veto_defs = [
            ("V1", "LP burned/locked"),
            ("V2", "Zero buy/sell tax"),
            ("V3", "No presale/VC"),
            ("V4", "No utility/roadmap"),
            ("V5", "Team wallet <10%"),
            ("V6", "Meme predates token"),
        ]
        veto_fails = set(result.get("vetoFails", []))
        for vid, vname in veto_defs:
            failed = vid in veto_fails
            status = "❌ FAIL" if failed else "✅ Pass"
            bg = "#fee2e2" if failed else "#f0fdf4"
            fg = "#991b1b" if failed else "#166534"
            st.markdown(f"""
            <div style='background:{bg}; border-radius:6px; padding:0.4rem 0.75rem; margin-bottom:0.3rem; display:flex; justify-content:space-between; font-size:0.82rem'>
                <span style='color:#475569'><strong>{vid}</strong> · {vname}</span>
                <span style='color:{fg}; font-weight:700'>{status}</span>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("#### Vs. $1B benchmarks")
        sorted_benches = sorted(BENCHMARKS, key=lambda b: abs(b["score"] - total))
        for b in sorted_benches:
            diff = total - b["score"]
            diff_str = "—" if vetoed else (f"+{diff}" if diff >= 0 else str(diff))
            diff_color = "#94a3b8" if vetoed else ("#16a34a" if diff >= 0 else "#dc2626")
            pct = b["score"] / 100
            st.markdown(f"""
            <div style='display:grid; grid-template-columns:55px 1fr 36px 36px; gap:8px; align-items:center; padding:4px 0; border-bottom:1px solid #f1f5f9; font-size:0.82rem'>
                <span style='font-weight:600; color:#1e293b'>{b["name"]}</span>
                <div style='background:#e2e8f0; border-radius:3px; height:4px; overflow:hidden'>
                    <div style='width:{b["score"]}%; height:100%; background:#6366f1; border-radius:3px'></div>
                </div>
                <span style='color:#94a3b8; text-align:right'>{b["score"]}</span>
                <span style='color:{diff_color}; font-weight:700; text-align:right'>{diff_str}</span>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("#### Runner indicator summary")
    st.info(result.get("runnerSummary", "No summary available."))

    st.markdown("""
    <div style='font-size:0.75rem; color:#94a3b8; margin-top:1rem'>
        AI-generated analysis based on the Inversal Framework derived from PEPE, WIF, PNUT, POPCAT, GOAT, BOME.
        Benchmark avg = 81/100. Not financial advice — crypto investing carries substantial risk of total loss.
    </div>
    """, unsafe_allow_html=True)

def render_live_feed_tab():
    st.markdown("## Live feed — pipeline candidates")
    st.markdown(
        "Logged pipeline candidates from `candidates.csv`. "
        "Use the filters below to narrow what you see — the slider only affects **already logged** tokens."
    )

    ctrl1, ctrl2, ctrl3 = st.columns([2, 1, 1])
    with ctrl1:
        chain_filter = st.selectbox(
            "Chain",
            ["All", "solana", "ethereum", "base", "bsc"],
            label_visibility="collapsed",
        )
    with ctrl2:
        min_score = st.slider("Min score", 50, 100, PIPELINE_SCORE_THRESHOLD, step=5)
    with ctrl3:
        if st.button("Refresh ↻", use_container_width=True):
            st.rerun()

    all_rows = load_candidates(200)
    rows = list(all_rows)
    if chain_filter != "All":
        rows = [r for r in rows if r.get("chain") == chain_filter]
    before_score_filter = len(rows)
    rows = [r for r in rows if int(r.get("score_total", 0)) >= min_score]

    if not all_rows:
        st.info("No candidates logged yet.")
        st.markdown(
            f"""
            The live feed only shows tokens that **both**:
            1. Pass all 6 DexScreener pre-filters, **and**
            2. Score **≥ {PIPELINE_SCORE_THRESHOLD}** when scanned (then logged to CSV)

            **Min score slider** ({min_score} selected) will filter the list once candidates exist.
            Right now there is nothing to filter.

            **Pre-filter window (new runners only):**
            - Mcap: **${MCAP_MIN/1e6:.0f}M–${MCAP_MAX/1e6:.0f}M**
            - Token age: **{TOKEN_AGE_MIN_HOURS}h–{TOKEN_AGE_MAX_HOURS}h** (1–7 days)
            - Liquidity ≥ $100K, buy/sell ratio ≥ 1.2, momentum + vol/mcap checks

            **BONK, PEPE, WIF, etc. will not appear here** — they are too large and too old.
            Use **Analyse a coin** (Tab 2) for established memecoins.

            Run **Manual search** in the sidebar, or start `python pipeline_runner.py --mode poll` in Terminal.
            """
        )
        return

    if not rows:
        st.warning(
            f"No candidates match your filters (min score **{min_score}**, chain **{chain_filter}**). "
            f"{before_score_filter} logged on this chain — try lowering min score."
        )
        return

    st.caption(f"Showing **{len(rows)}** of **{len(all_rows)}** logged candidates (min score ≥ {min_score})")

    m1, m2, m3, m4 = st.columns(4)
    scores = [int(r.get("score_total", 0)) for r in rows]
    strong = sum(1 for s in scores if s >= 85)
    avg_s = sum(scores) / len(scores) if scores else 0
    chains = [r.get("chain", "") for r in rows]
    top_chain = max(set(chains), key=chains.count) if chains else "—"
    m1.metric("Candidates", len(rows))
    m2.metric("Strong signal (≥85)", strong)
    m3.metric("Avg score", f"{avg_s:.0f}")
    m4.metric("Top chain", top_chain)

    st.markdown("---")

    for row in rows:
        score = int(row.get("score_total", 0))
        vetoed = str(row.get("vetoed", "False")).lower() == "true"
        verdict_text, verdict_class = get_verdict(score, vetoed)
        sc = score_color(score, vetoed)
        gap = score - AVG_BENCHMARK
        gap_str = f"+{gap}" if gap >= 0 else str(gap)

        with st.expander(
            f"**{row.get('ticker', '?')}** · {row.get('chain', '?')} · "
            f"Score: {score}/100 · {verdict_text} · Gap: {gap_str}",
            expanded=False,
        ):
            c1, c2, c3 = st.columns([2, 2, 1])

            with c1:
                st.markdown(f"**{row.get('name', '?')}** ({row.get('ticker', '?')})")
                st.caption(
                    f"{row.get('chain', '?')} · Mcap {row.get('current_mcap', '?')} · "
                    f"{row.get('timestamp', '')}"
                )
                liq_k = parse_liquidity_usd(row.get("liquidity_usd", "0")) / 1e3
                st.markdown(
                    f"Liq: **${liq_k:.0f}K** · "
                    f"Vol/mcap: **{row.get('vol_mcap_ratio', '?')}** · "
                    f"Buy/sell: **{row.get('buyer_sell_ratio', '?')}** · "
                    f"1h: **{row.get('price_change_1h', '?')}** · "
                    f"6h: **{row.get('price_change_6h', '?')}**"
                )

            with c2:
                section_vals = [
                    ("A", int(row.get("score_a", 0)), 25),
                    ("B", int(row.get("score_b", 0)), 25),
                    ("C", int(row.get("score_c", 0)), 25),
                    ("D", int(row.get("score_d", 0)), 15),
                    ("E", int(row.get("score_e", 0)), 10),
                ]
                for sid, val, smax in section_vals:
                    bc1, bc2 = st.columns([3, 1])
                    with bc1:
                        st.progress(val / smax)
                    with bc2:
                        st.caption(f"{sid} {val}")

            with c3:
                st.markdown(
                    f"<div style='font-size:2.5rem;font-weight:800;color:{sc};text-align:center;line-height:1'>{score}</div>"
                    f"<div style='text-align:center'><span class='verdict-pill {verdict_class}'>{verdict_text}</span></div>",
                    unsafe_allow_html=True,
                )
                if row.get("pair_url"):
                    st.link_button("DexScreener ↗", row["pair_url"], use_container_width=True)
                if st.button(
                    "Re-analyse ↗",
                    key=f"ra_{row.get('pair_address', '')}",
                    use_container_width=True,
                ):
                    st.session_state["prefill_query"] = row.get("ticker", "")
                    st.rerun()

            if row.get("runner_summary"):
                st.info(row["runner_summary"])

            if row.get("veto_fails"):
                st.error(f"Veto fails: {row['veto_fails']}")

def render_weekly_report_tab():
    st.markdown("## Weekly report — 30-day trends")
    st.markdown(
        f"Monday pipeline snapshots appended to `{WEEKLY_REPORT_XLSX}`. "
        f"Track tokens that keep appearing and **rising** over several weeks."
    )

    meta = get_report_meta()
    if meta:
        st.caption(
            f"Last run: **{meta.get('last_run', '—')}** · "
            f"Last batch: **{int(meta.get('rows_appended', 0))}** tokens"
        )

    lookback = st.slider("Lookback (days)", 7, 90, TREND_LOOKBACK_DAYS, step=7)
    snapshots = load_snapshots(days=lookback)
    trends = compute_trends(snapshots)

    if snapshots.empty:
        st.info("No weekly report data yet.")
        st.markdown(
            """
            **Setup (one time):**
            ```bash
            cd /Users/Laura/Downloads/meme_alerts
            chmod +x install_weekly_cron.sh weekly_run.sh
            ./install_weekly_cron.sh   # Mondays 9:00 AM
            ```

            **Run manually now:**
            ```bash
            ./weekly_run.sh
            ```
            Or use **Run weekly report now** in the sidebar under Pipeline.
            """
        )
        return

    trending = trends[trends["trending"] == True] if not trends.empty else trends  # noqa: E712
    near = trends[trends["near_breakout"] == True] if not trends.empty else trends  # noqa: E712

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Snapshot rows", len(snapshots))
    m2.metric("Unique tokens", trends["ticker"].nunique() if not trends.empty else 0)
    m3.metric("Trending up", len(trending))
    m4.metric("Near breakout (≥65)", len(near))

    st.markdown("---")
    st.markdown("### Trending tokens")
    st.caption(
        "**Trending** = seen on 2+ Mondays with score up ≥3 pts. "
        "**Streak up** = score improved every week tracked."
    )

    show_trending_only = st.checkbox("Show trending only", value=False)

    display = trends.copy()
    if show_trending_only and not display.empty:
        display = display[display["trending"] == True]  # noqa: E712

    if display.empty:
        st.warning("No multi-week trends in this window yet. Check back after 2+ Monday runs.")
    else:
        table_cols = [
            "ticker", "chain", "appearances", "score_first", "score_latest",
            "score_delta", "trend", "verdict_latest", "last_seen",
        ]
        st.dataframe(
            display[table_cols],
            use_container_width=True,
            hide_index=True,
        )

        labels = [
            f"{r['ticker']} ({r['chain']}) — {r['trend']}"
            for _, r in display.iterrows()
        ]
        pick = st.selectbox("Score history", options=labels, label_visibility="collapsed")
        if pick:
            row = display.iloc[labels.index(pick)]
            chart_df = pd.DataFrame({"score": row["score_history"]}, index=row["date_history"])
            st.line_chart(chart_df)
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"**{row['name']}** ({row['ticker']}) · {row['chain']}")
                st.caption(
                    f"Seen **{row['appearances']}** times · "
                    f"{row['first_seen']} → {row['last_seen']}"
                )
            with c2:
                url = row.get("pair_url") if hasattr(row, "get") else row["pair_url"]
                if url and str(url) != "nan":
                    st.link_button("DexScreener ↗", url)

    st.markdown("---")
    st.markdown("### Raw weekly snapshots")
    chain_f = st.selectbox(
        "Filter chain",
        ["All"] + sorted(snapshots["chain"].dropna().unique().tolist()),
        key="weekly_chain_filter",
    )
    view = snapshots.copy()
    if chain_f != "All":
        view = view[view["chain"] == chain_f]
    view = view.sort_values("report_date", ascending=False)
    raw_cols = [
        "report_date", "ticker", "chain", "score_total", "verdict",
        "runner_gap", "market_cap_usd", "liquidity_usd",
    ]
    st.dataframe(view[raw_cols], use_container_width=True, hide_index=True)

def render_ath_row_card(row, verdict_style):
    bg, fg, icon = verdict_style.get(row["verdict"], ("#f1f5f9", "#64748b", "⬛"))
    pct = row["pct_to_ath"]
    if pct.startswith("+"):
        pct_color = "#16a34a"
    elif pct.startswith("-"):
        pct_color = "#dc2626"
    else:
        pct_color = "#64748b"
    extra = ""
    if row.get("target_2x"):
        extra = f" · <strong>2x target: {row['target_2x']}</strong>"
    return f"""
    <article class="ath-card">
        <header class="ath-card-header">
            <span class="ath-ticker">{row['ticker']}</span>
            <span class="ath-badge" style="background:{bg};color:{fg}">{icon} {row['verdict']}</span>
        </header>
        <div class="ath-name">{row['name']}</div>
        <dl class="ath-stats">
            <div><dt>Price Jun 26</dt><dd>{row['price_jun26']}</dd></div>
            <div><dt>ATH</dt><dd>{row['ath']}</dd></div>
            <div><dt>% to ATH</dt><dd style="color:{pct_color}">{pct}</dd></div>
        </dl>
        <p class="ath-notes">{row['notes']}{extra}</p>
    </article>
    """

def render_ath_tracker_tab():
    st.markdown("## ATH recovery tracker")
    st.markdown(
        "All assets from the Jun 26 2026 ATH analysis. "
        "Post-Oct 2025 cycle high used as ATH reference unless noted. "
        "Data as of June 26, 2026."
    )

    f1, f2, f3 = st.columns([2, 2, 2])
    batch_options = ["All", *ATH_BATCHES]
    if st.session_state.get("ath_batch_filter") not in batch_options:
        st.session_state["ath_batch_filter"] = "All"

    verdict_options = [
        "Already exceeded ATH", "Already near ATH", "Likely (bull cycle)",
        "Likely", "Possible", "Unlikely",
    ]
    if "ath_verdict_filter" in st.session_state:
        st.session_state["ath_verdict_filter"] = [
            v for v in st.session_state["ath_verdict_filter"] if v in verdict_options
        ] or verdict_options[:-1]

    with f1:
        batch_filter_raw = st.selectbox(
            "Batch",
            batch_options,
            label_visibility="visible",
            key="ath_batch_filter",
        )
        batch_filter = normalize_batch_filter(batch_filter_raw)
    with f2:
        verdict_filter = st.multiselect(
            "Verdict",
            verdict_options,
            default=verdict_options[:-1],
            key="ath_verdict_filter",
        )
    with f3:
        search_q = st.text_input("Search ticker or name", placeholder="e.g. SOL")

    rows = list(ATH_DATA)
    if batch_filter != "All":
        rows = [r for r in rows if r["batch"] == batch_filter]
    if verdict_filter:
        allowed = set(verdict_filter)
        rows = [r for r in rows if r["verdict"] in allowed]
    if search_q.strip():
        q = search_q.strip().upper()
        rows = [
            r for r in rows
            if q in r["ticker"].upper() or q in r["name"].upper()
        ]

    rows = sorted(rows, key=lambda r: (VERDICT_ORDER.get(r["verdict"], 9), r["ticker"]))

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Total shown", len(rows))
    m2.metric(
        "Already at/exceeded ATH",
        sum(
            1 for r in rows
            if "exceeded" in r["verdict"].lower() or "near" in r["verdict"].lower()
        ),
    )
    m3.metric("Likely", sum(1 for r in rows if "likely" in r["verdict"].lower()))
    m4.metric("Possible", sum(1 for r in rows if r["verdict"] == "Possible"))
    m5.metric("Unlikely", sum(1 for r in rows if r["verdict"] == "Unlikely"))

    st.markdown("---")

    verdict_style = {
        "Already exceeded ATH": ("#d1fae5", "#065f46", "⬆"),
        "Already near ATH": ("#d1fae5", "#065f46", "✅"),
        "Likely (bull cycle)": ("#dcfce7", "#166534", "🟢"),
        "Likely": ("#dcfce7", "#166534", "🟢"),
        "Possible": ("#fef3c7", "#92400e", "🟡"),
        "Unlikely": ("#fee2e2", "#991b1b", "🔴"),
        "No data": ("#f1f5f9", "#64748b", "⬛"),
    }

    if rows:
        cards_html = "".join(render_ath_row_card(row, verdict_style) for row in rows)
        st.markdown(f'<div class="ath-list">{cards_html}</div>', unsafe_allow_html=True)
    else:
        st.info("No assets match the current filters.")

    st.markdown("---")
    st.markdown(
        "<div style='font-size:0.75rem;color:#94a3b8;line-height:1.8'>"
        "⬆ Already exceeded ATH &nbsp;·&nbsp; "
        "✅ Already near ATH (within 5%) &nbsp;·&nbsp; "
        "🟢 Likely — strong fundamentals, manageable gap &nbsp;·&nbsp; "
        "🟡 Possible — needs macro tailwind or alt season &nbsp;·&nbsp; "
        "🔴 Unlikely — structural headwinds or extreme gap<br>"
        "ATH reference: post-October 2025 cycle high unless noted. "
        "Data as of June 26, 2026. Not financial advice."
        "</div>",
        unsafe_allow_html=True,
    )

def main():
    with st.sidebar:
        st.markdown("### Pipeline")

        pipeline_mode = st.radio(
            "Mode",
            ["Off", "Poll (5 min)", "Stream (30s)", "Manual search"],
            help="Poll: scans all chains every 5 min. Stream: fast scans boosted pairs. Manual: search a specific token.",
        )

        if pipeline_mode == "Manual search":
            st.caption(
                f"Targets **new runners**: mcap ${MCAP_MIN/1e6:.0f}M–${MCAP_MAX/1e6:.0f}M, "
                f"age {TOKEN_AGE_MIN_HOURS}h–{TOKEN_AGE_MAX_HOURS}h. "
                f"Use Tab 2 for coins like BONK."
            )
            manual_q = st.text_input("Token name or address", placeholder="e.g. BONK or 0x...")
            run_manual = st.button("Scan ↗", type="primary", use_container_width=True)
            if run_manual and manual_q.strip():
                api_key = get_api_key()
                if not api_key:
                    st.sidebar.error("Scan unavailable — server API key not configured.")
                else:
                    with st.spinner(f"Scanning {manual_q}..."):
                        pairs = search_dex_pairs(
                            manual_q.strip(),
                            on_warning=lambda msg: st.sidebar.warning(msg),
                        )
                        summaries = summarize_pre_filter(pairs)
                        st.session_state.last_scan_summaries = summaries
                        filtered = [
                            pair for pair, summary in zip(pairs, summaries)
                            if summary["passed"]
                        ]
                        for pair in filtered[:5]:
                            quant = quant_score(pair)
                            result = score_coin_hybrid(pair, quant, api_key=api_key)
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
                            else:
                                st.sidebar.error(f"{pair.token_symbol}: scoring failed (API error)")
                        if pairs and not filtered:
                            st.sidebar.warning(
                                f"Found {len(pairs)} pairs via DexScreener — none match the "
                                f"new-runner pre-filters (${MCAP_MIN/1e6:.0f}M–${MCAP_MAX/1e6:.0f}M mcap, "
                                f"{TOKEN_AGE_MIN_HOURS}h–{TOKEN_AGE_MAX_HOURS}h age)."
                            )
                            with st.sidebar.expander("Why each pair failed", expanded=True):
                                for s in summaries:
                                    st.caption(
                                        f"**{s['symbol']}** ({s['chain']}) · "
                                        f"mcap ${s['market_cap']/1e6:.1f}M · age {s['age_hours']:.0f}h\n\n"
                                        f"{s['reason']}"
                                    )
                        elif not pairs:
                            st.sidebar.warning(f"No pairs found for '{manual_q}'")

        elif pipeline_mode in ("Poll (5 min)", "Stream (30s)"):
            st.info(
                "Automated polling runs as a background process. "
                "Start it from the terminal:\n\n"
                "```\npython pipeline_runner.py --mode poll\n```"
            )
            st.caption("The live feed tab updates as candidates are logged to candidates.csv")

        rows = load_candidates(1000)
        if rows:
            st.markdown("---")
            st.caption(f"**{len(rows)}** candidates logged · last: {rows[0].get('timestamp', '')}")

        st.markdown("---")
        st.markdown("### Weekly report")
        st.caption("Runs every Monday (cron). Appends to weekly_report.xlsx.")
        if st.button("Run weekly report now ↗", use_container_width=True):
            api_key = get_api_key()
            if not api_key:
                st.sidebar.error("Weekly scan unavailable — server API key not configured.")
            else:
                with st.spinner("Running weekly scan across all chains..."):
                    try:
                        results = run_weekly_scan(api_key=api_key)
                        st.sidebar.success(
                            f"Weekly report updated — {len(results)} tokens appended."
                        )
                    except Exception as exc:
                        st.sidebar.error(f"Weekly run failed: {exc}")

    st.markdown("# 🪙 Memecoin runner indicator")
    st.markdown("<div style='color:#64748b; margin-top:-0.5rem; margin-bottom:1.5rem'>Inversal framework · $1B+ benchmark cohort · June 2026</div>", unsafe_allow_html=True)

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📖 Framework",
        "🔍 Analyse",
        "📡 Live feed",
        "📊 Weekly",
        "📈 ATH",
    ])

    with tab1:
        render_methodology_tab()

    with tab2:
        render_analyser_tab()

    with tab3:
        render_live_feed_tab()

    with tab4:
        render_weekly_report_tab()

    with tab5:
        render_ath_tracker_tab()

if __name__ == "__main__":
    main()
