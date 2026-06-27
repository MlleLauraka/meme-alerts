# Memecoin Runner Indicator

A Streamlit app that scores any memecoin against the Inversal Framework — a methodology derived from every confirmed $1B+ memecoin — and produces a runner indicator showing how a candidate compares to the benchmark cohort (PEPE, WIF, PNUT, POPCAT, GOAT, BOME).

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Set your Anthropic API key

The app uses Claude to score coins. Set your key as an environment variable:

```bash
# macOS / Linux
export ANTHROPIC_API_KEY="sk-ant-..."

# Windows (Command Prompt)
set ANTHROPIC_API_KEY=sk-ant-...

# Windows (PowerShell)
$env:ANTHROPIC_API_KEY="sk-ant-..."
```

Or create a `.env` file in the project folder:
```
ANTHROPIC_API_KEY=sk-ant-...
```

### 3. Run the app

```bash
./run.sh
```

Or:

```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`

---

## Pipeline

The DexScreener pipeline scans live pairs, applies 6 hard pre-filters (no AI cost), then hybrid-scores survivors: sections C and E1 from on-chain data, sections A/B/D/E2 and veto checks via Claude.

### Manual scan (in app)

1. Open the sidebar → **Pipeline** → **Manual search**
2. Enter a token name or address and click **Scan ↗**
3. Passing candidates (score ≥ 70) are logged to `candidates.csv` and appear on the **Live feed** tab

### Background polling (terminal)

```bash
python pipeline_runner.py --mode poll
python pipeline_runner.py --mode stream --chains solana,base
```

- **poll**: scans all chains every 5 minutes
- **stream**: scans every 30 seconds with pair deduplication

### Weekly report (Mondays)

Every Monday the pipeline re-runs across all chains and **appends** results to `weekly_report.xlsx`.

**One-time schedule (macOS cron, Mondays 9:00 AM):**
```bash
chmod +x install_weekly_cron.sh weekly_run.sh
./install_weekly_cron.sh
```

**Run manually:**
```bash
./weekly_run.sh
```

Or click **Run weekly report now** in the app sidebar.

The **Weekly report** tab shows the last 30 days of snapshots and highlights tokens **trending up** across multiple Mondays (score rising over several weeks).

---

## Project structure

```
meme_alerts/
├── app.py               # Streamlit UI
├── pipeline.py          # DexScreener fetch, pre-filter, quant + hybrid scoring, CSV log
├── pipeline_runner.py   # Background poll/stream runner
├── weekly_report.py     # Monday Excel append + trend analysis
├── weekly_runner.py     # CLI for weekly scan
├── weekly_run.sh        # Weekly scan launcher (proxy-safe)
├── install_weekly_cron.sh  # Install Monday 9am cron job
├── ath_data.py          # Embedded ATH tracker dataset
├── run.sh               # Start app (clears proxy vars)
├── requirements.txt
├── candidates.csv       # Logged pipeline candidates (gitignored)
├── weekly_report.xlsx   # Monday snapshots (gitignored)
└── README.md
```

---

## The five tabs

### Tab 1 — Methodology and framework
Explains the full Inversal Framework:
- How the method works (top-down from $1B outcomes)
- All 5 scoring sections (A–E) with criteria and point breakdowns
- The 6 veto checks and why each one matters
- Verdict thresholds (Strong signal / Promising / Speculative / Do not proceed / Disqualified)
- The full verified $1B+ benchmark cohort with scores

### Tab 2 — Analyse a coin
Live scoring interface:
- Type any coin ticker or name and click Analyse
- 10 quick-pick buttons for common coins (BONK, SHIB, FLOKI, etc.)
- Full section breakdown (A–E bars with scores)
- Veto check results (Pass / Fail for all 6)
- Key findings (positive / mixed / negative)
- Runner gap vs $1B cohort average (81/100)
- Comparison against all 6 benchmark coins
- Session history in the sidebar for re-loading previous results

### Tab 3 — Live feed
Pipeline candidates from `candidates.csv`:
- Filter by chain and minimum score
- Section score bars, verdict, runner gap
- DexScreener link and re-analyse shortcut

### Tab 4 — Weekly report
Monday pipeline snapshots from `weekly_report.xlsx`:
- 30-day lookback with adjustable window
- Trending tokens (multi-week score rise)
- Per-token score history charts
- Raw snapshot table

### Tab 5 — ATH Tracker
63 assets from the Jun 2026 ATH analysis (embedded data):
- Batch filter (Top 100 3x><5x, Top 100 >5x, 2x +potential ATH)
- Verdict filter and ticker/name search
- Colour-coded % to ATH and 2x targets for Batch 4

---

## Framework summary

The Inversal Method works backward from confirmed $1B outcomes to identify necessary conditions:

| Section | Max pts | What it measures |
|---|---|---|
| A · Meme foundation | 25 | Pre-existing viral meme, emotional charge, remixability |
| B · Token structure | 25 | LP burned, contract renounced, clean supply distribution |
| C · Organic growth | 25 | Holder velocity, volume/mcap ratio, community spontaneity |
| D · Cycle fit | 15 | Bitcoin halving proximity, archetype novelty |
| E · Launch velocity | 10 | 72hr price action, organic influencer pickup |

**Runner gap** = Candidate score − 81 (cohort average)
- Positive = above $1B benchmark profile
- Within −7 = inside historical range of confirmed $1B coins
- Below −7 = structural gap to close

---

## Notes

- Scores are AI-generated based on Claude's training knowledge. Data quality decreases for very new or obscure coins — confidence level is flagged in each result.
- This is not financial advice. Crypto investing carries substantial risk of total loss.
- The framework applies to pure memecoins only. AI infrastructure tokens, NFT projects with utility, and governance tokens fall outside the model's scope.
