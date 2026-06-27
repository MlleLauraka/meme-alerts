# ATH Tracker — Cursor prompt

Add a fourth tab "📊 ATH Tracker" to the existing app.py.
The data is embedded directly — no external file dependency.

---

## Step 1 — Add the data constant

In app.py, after the BENCHMARKS constant block, add:

```python
# ── ATH Tracker data (source: Crypto_ATH_Analysis_Jun2026.xlsx) ──────────────
ATH_DATA = [
    # Batch 1 — Major Alts + SPX
    # Already at / near ATH
    {"ticker":"SPX",     "name":"S&P 500 Index",                              "batch":"Major Alts",    "category":"Already near ATH", "price_jun26":"$7,350",      "ath":"$7,621",       "pct_to_ath":"-3.5%",  "verdict":"Already near ATH", "notes":"S&P 500 Index"},
    # Likely
    {"ticker":"SOL",     "name":"Solana",                                     "batch":"Major Alts",    "category":"Likely",           "price_jun26":"~$70",        "ath":"~$295",        "pct_to_ath":"-76%",   "verdict":"Likely",           "notes":"Layer 1 · High utility · ETF / treasury adoption"},
    {"ticker":"LINK",    "name":"Chainlink",                                  "batch":"Major Alts",    "category":"Likely",           "price_jun26":"~$7.30",      "ath":"~$14",         "pct_to_ath":"-48%",   "verdict":"Likely",           "notes":"Oracle infra · 47-bank RWA settlement · 2x target"},
    {"ticker":"AAVE",    "name":"Aave",                                       "batch":"Major Alts",    "category":"Likely",           "price_jun26":"~$140",       "ath":"~$340",        "pct_to_ath":"-59%",   "verdict":"Likely",           "notes":"DeFi lending · Kraken 15% stake talks"},
    {"ticker":"OKB",     "name":"OKB",                                        "batch":"Major Alts",    "category":"Likely",           "price_jun26":"~$38",        "ath":"~$65",         "pct_to_ath":"-42%",   "verdict":"Likely",           "notes":"OKX exchange token · buy-burn"},
    {"ticker":"ONDO",    "name":"Ondo Finance",                               "batch":"Major Alts",    "category":"Likely",           "price_jun26":"~$0.36",      "ath":"~$0.90",       "pct_to_ath":"-60%",   "verdict":"Likely",           "notes":"RWA tokenization leader"},
    {"ticker":"BGB",     "name":"Bitget Token",                               "batch":"Major Alts",    "category":"Likely",           "price_jun26":"~$3.80",      "ath":"~$9.00",       "pct_to_ath":"-58%",   "verdict":"Likely",           "notes":"Bitget exchange token"},
    # Possible
    {"ticker":"DOGE",    "name":"Dogecoin",                                   "batch":"Major Alts",    "category":"Possible",         "price_jun26":"~$0.10",      "ath":"~$0.48",       "pct_to_ath":"-79%",   "verdict":"Possible",         "notes":"OG meme / payments · Elon factor"},
    {"ticker":"HBAR",    "name":"Hedera",                                     "batch":"Major Alts",    "category":"Possible",         "price_jun26":"~$0.078",     "ath":"~$0.40",       "pct_to_ath":"-80%",   "verdict":"Possible",         "notes":"Enterprise DLT · ETF approved"},
    {"ticker":"BCH",     "name":"Bitcoin Cash",                               "batch":"Major Alts",    "category":"Possible",         "price_jun26":"~$380",       "ath":"~$800",        "pct_to_ath":"-52%",   "verdict":"Possible",         "notes":"Payments fork · fading relevance"},
    {"ticker":"PEPE",    "name":"Pepe",                                       "batch":"Major Alts",    "category":"Possible",         "price_jun26":"~$0.0000070", "ath":"~$0.000027",   "pct_to_ath":"-74%",   "verdict":"Possible",         "notes":"Top meme by volume · cultural staying power"},
    {"ticker":"AVAX",    "name":"Avalanche",                                  "batch":"Major Alts",    "category":"Possible",         "price_jun26":"~$6.50",      "ath":"~$45",         "pct_to_ath":"-86%",   "verdict":"Possible",         "notes":"Layer 1 · Subnet ecosystem"},
    {"ticker":"FET",     "name":"Fetch.ai",                                   "batch":"Major Alts",    "category":"Possible",         "price_jun26":"~$0.50",      "ath":"~$3.40",       "pct_to_ath":"-85%",   "verdict":"Possible",         "notes":"AI agents · ASI Alliance"},
    {"ticker":"CRO",     "name":"Cronos",                                     "batch":"Major Alts",    "category":"Possible",         "price_jun26":"~$0.070",     "ath":"~$0.22",       "pct_to_ath":"-68%",   "verdict":"Possible",         "notes":"Crypto.com ecosystem · consumer"},
    {"ticker":"SHIB",    "name":"Shiba Inu",                                  "batch":"Major Alts",    "category":"Possible",         "price_jun26":"~$0.0000050", "ath":"~$0.000015",   "pct_to_ath":"-67%",   "verdict":"Possible",         "notes":"Shibarium L2 · large community"},
    {"ticker":"TIA",     "name":"Celestia",                                   "batch":"Major Alts",    "category":"Possible",         "price_jun26":"~$1.80",      "ath":"~$8.00",       "pct_to_ath":"-77%",   "verdict":"Possible",         "notes":"Modular DA layer"},
    {"ticker":"POL",     "name":"Polygon (rebranded)",                        "batch":"Major Alts",    "category":"Possible",         "price_jun26":"~$0.19",      "ath":"~$0.72",       "pct_to_ath":"-74%",   "verdict":"Possible",         "notes":"Polygon rebranded · L2 infra"},
    {"ticker":"ASTER",   "name":"Astar",                                      "batch":"Major Alts",    "category":"Possible",         "price_jun26":"~$0.12",      "ath":"~$0.50",       "pct_to_ath":"-76%",   "verdict":"Possible",         "notes":"AI infra / compute"},
    {"ticker":"FIL",     "name":"Filecoin",                                   "batch":"Major Alts",    "category":"Possible",         "price_jun26":"~$2.20",      "ath":"~$8.00",       "pct_to_ath":"-72%",   "verdict":"Possible",         "notes":"Decentralized storage"},
    # Unlikely
    {"ticker":"FLR",     "name":"Flare",                                      "batch":"Major Alts",    "category":"Unlikely",         "price_jun26":"~$0.012",     "ath":"~$0.058",      "pct_to_ath":"-79%",   "verdict":"Unlikely",         "notes":"Cross-chain oracle · weak demand"},
    {"ticker":"TRUMP",   "name":"Official Trump",                             "batch":"Major Alts",    "category":"Unlikely",         "price_jun26":"~$1.68",      "ath":"~$74",         "pct_to_ath":"-98%",   "verdict":"Unlikely",         "notes":"Meme/political · -98% · token unlocks · insider losses"},
    {"ticker":"WLFI",    "name":"World Liberty Financial",                    "batch":"Major Alts",    "category":"Unlikely",         "price_jun26":"~$0.11",      "ath":"~$0.18",       "pct_to_ath":"-39%",   "verdict":"Unlikely",         "notes":"DeFi / Trump-linked governance · illiquid"},
    {"ticker":"PUMP",    "name":"Pump.fun",                                   "batch":"Major Alts",    "category":"Unlikely",         "price_jun26":"~$0.003",     "ath":"~$0.016",      "pct_to_ath":"-81%",   "verdict":"Unlikely",         "notes":"pump.fun token · launchpad hype cooled"},
    {"ticker":"SPX6900", "name":"SPX6900",                                    "batch":"Major Alts",    "category":"Unlikely",         "price_jun26":"~$0.33",      "ath":"~$2.27",       "pct_to_ath":"-85%",   "verdict":"Unlikely",         "notes":"Meme coin · community thin"},

    # Batch 2 — Layer 1s & DeFi
    # Possible
    {"ticker":"SUI",     "name":"Sui",                                        "batch":"L1s & DeFi",   "category":"Possible",         "price_jun26":"~$0.69",      "ath":"~$5.35",       "pct_to_ath":"-87%",   "verdict":"Possible",         "notes":"L1 · Strong ecosystem · Cetus hack overhang"},
    {"ticker":"ENA",     "name":"Ethena",                                     "batch":"L1s & DeFi",   "category":"Possible",         "price_jun26":"~$0.08",      "ath":"~$0.50",       "pct_to_ath":"-84%",   "verdict":"Possible",         "notes":"Synthetic dollar · fee switch · unlock pressure"},
    {"ticker":"ADA",     "name":"Cardano",                                    "batch":"L1s & DeFi",   "category":"Possible",         "price_jun26":"~$0.147",     "ath":"~$1.25",       "pct_to_ath":"-88%",   "verdict":"Possible",         "notes":"L1 · Large supply · fading narrative"},
    {"ticker":"VET",     "name":"VeChain",                                    "batch":"L1s & DeFi",   "category":"Possible",         "price_jun26":"~$0.016",     "ath":"~$0.055",      "pct_to_ath":"-71%",   "verdict":"Possible",         "notes":"Enterprise supply chain · low traction"},
    {"ticker":"MNT",     "name":"Mantle",                                     "batch":"L1s & DeFi",   "category":"Possible",         "price_jun26":"~$0.45",      "ath":"~$1.40",       "pct_to_ath":"-68%",   "verdict":"Possible",         "notes":"Mantle L2 · Bybit-backed · shrinking TVL"},
    {"ticker":"ETHFI",   "name":"Ether.fi",                                   "batch":"L1s & DeFi",   "category":"Possible",         "price_jun26":"~$0.37",      "ath":"~$3.00",       "pct_to_ath":"-88%",   "verdict":"Possible",         "notes":"Liquid restaking · niche DeFi"},
    # Unlikely
    {"ticker":"APT",     "name":"Aptos",                                      "batch":"L1s & DeFi",   "category":"Unlikely",         "price_jun26":"~$0.58",      "ath":"~$13.91",      "pct_to_ath":"-96%",   "verdict":"Unlikely",         "notes":"L1 · supply inflation · lost to SUI"},
    {"ticker":"ARB",     "name":"Arbitrum",                                   "batch":"L1s & DeFi",   "category":"Unlikely",         "price_jun26":"~$0.076",     "ath":"~$0.72",       "pct_to_ath":"-89%",   "verdict":"Unlikely",         "notes":"L2 governance token · no fee accrual"},
    {"ticker":"SEI",     "name":"Sei",                                        "batch":"L1s & DeFi",   "category":"Unlikely",         "price_jun26":"~$0.050",     "ath":"~$0.60",       "pct_to_ath":"-92%",   "verdict":"Unlikely",         "notes":"L1 · exchange chain · struggling traction"},
    {"ticker":"DOT",     "name":"Polkadot",                                   "batch":"L1s & DeFi",   "category":"Unlikely",         "price_jun26":"~$0.85",      "ath":"~$7.98",       "pct_to_ath":"-89%",   "verdict":"Unlikely",         "notes":"L0 · lost developer mindshare · near ATL"},
    {"ticker":"PENGU",   "name":"Pudgy Penguins",                             "batch":"L1s & DeFi",   "category":"Unlikely",         "price_jun26":"~$0.006",     "ath":"~$0.048",      "pct_to_ath":"-88%",   "verdict":"Unlikely",         "notes":"NFT meme token · no utility catalyst"},
    {"ticker":"BONK",    "name":"Bonk",                                       "batch":"L1s & DeFi",   "category":"Unlikely",         "price_jun26":"~$0.0000090", "ath":"~$0.000060",   "pct_to_ath":"-85%",   "verdict":"Unlikely",         "notes":"Solana OG meme · hype cycle exhausted"},

    # Batch 3 — Meme Coins
    # Possible
    {"ticker":"FLOKI",   "name":"Floki",                                      "batch":"Meme Coins",   "category":"Possible",         "price_jun26":"~$0.000024",  "ath":"~$0.00013",    "pct_to_ath":"-82%",   "verdict":"Possible",         "notes":"Meme + utility · Valhalla game live · MiCAR compliant"},
    {"ticker":"ORDI",    "name":"Ordinals",                                   "batch":"Meme Coins",   "category":"Possible",         "price_jun26":"~$3.20",      "ath":"~$20",         "pct_to_ath":"-84%",   "verdict":"Possible",         "notes":"BRC-20 pioneer · Bitcoin-correlated"},
    {"ticker":"DEGEN",   "name":"Degen",                                      "batch":"Meme Coins",   "category":"Possible",         "price_jun26":"~$0.0009",    "ath":"~$0.025",      "pct_to_ath":"-96%",   "verdict":"Possible",         "notes":"Base/Farcaster gas token · real utility · ~$33M mcap"},
    # Unlikely
    {"ticker":"WIF",     "name":"Dogwifhat",                                  "batch":"Meme Coins",   "category":"Unlikely",         "price_jun26":"~$0.14",      "ath":"~$4.85",       "pct_to_ath":"-97%",   "verdict":"Unlikely",         "notes":"Solana dog meme · Sphere project abandoned"},
    {"ticker":"FARTCOIN","name":"Fartcoin",                                   "batch":"Meme Coins",   "category":"Unlikely",         "price_jun26":"~$0.16",      "ath":"~$1.80",       "pct_to_ath":"-91%",   "verdict":"Unlikely",         "notes":"Absurdist Solana meme · novelty faded"},
    {"ticker":"POPCAT",  "name":"Popcat",                                     "batch":"Meme Coins",   "category":"Unlikely",         "price_jun26":"~$0.04",      "ath":"~$1.75",       "pct_to_ath":"-98%",   "verdict":"Unlikely",         "notes":"Solana cat meme · $50M mcap"},
    {"ticker":"MELANIA", "name":"Melania Meme",                               "batch":"Meme Coins",   "category":"Unlikely",         "price_jun26":"~$0.075",     "ath":"~$13",         "pct_to_ath":"-99%",   "verdict":"Unlikely",         "notes":"Political meme · same structural issues as TRUMP"},
    {"ticker":"DOG",     "name":"Dog (Rune)",                                 "batch":"Meme Coins",   "category":"Unlikely",         "price_jun26":"~$0.0008",    "ath":"~$0.012",      "pct_to_ath":"-93%",   "verdict":"Unlikely",         "notes":"Bitcoin Rune · BTC-correlated meme"},

    # Batch 4 — 2x ATH targets (volatile crypto only; stables/T-bills excluded)
    # Already near / exceeded ATH
    {"ticker":"HYPE",    "name":"Hyperliquid",                                "batch":"2x ATH",       "category":"Already near ATH", "price_jun26":"~$64",        "ath":"~$77",         "pct_to_ath":"n/a",    "verdict":"Already near ATH", "notes":"Hyperliquid · on-chain perps · just hit ATH ~$77",   "target_2x":"~$154"},
    {"ticker":"XMR",     "name":"Monero",                                     "batch":"2x ATH",       "category":"Already exceeded", "price_jun26":"~$320",       "ath":"~$230",        "pct_to_ath":"+39%",   "verdict":"Already exceeded ATH","notes":"Monero · privacy · exceeded Oct '25 ATH",            "target_2x":"~$460"},
    {"ticker":"XAUT",    "name":"Tether Gold",                                "batch":"2x ATH",       "category":"Already exceeded", "price_jun26":"~$3,340",     "ath":"~$2,650",      "pct_to_ath":"+26%",   "verdict":"Already exceeded ATH","notes":"Tether Gold · 1 troy oz gold",                        "target_2x":"~$5,300"},
    {"ticker":"PAXG",    "name":"Paxos Gold",                                 "batch":"2x ATH",       "category":"Already exceeded", "price_jun26":"~$3,340",     "ath":"~$2,650",      "pct_to_ath":"+26%",   "verdict":"Already exceeded ATH","notes":"Paxos Gold",                                          "target_2x":"~$5,300"},
    {"ticker":"ZEC",     "name":"Zcash",                                      "batch":"2x ATH",       "category":"Already exceeded", "price_jun26":"~$418",       "ath":"~$60",         "pct_to_ath":"+597%",  "verdict":"Already exceeded ATH","notes":"Zcash · privacy coin · well above Oct '25 level",     "target_2x":"~$120"},
    # Likely (bull cycle)
    {"ticker":"BTC",     "name":"Bitcoin",                                    "batch":"2x ATH",       "category":"Likely",           "price_jun26":"~$60,000",    "ath":"~$126,000",    "pct_to_ath":"-52%",   "verdict":"Likely (bull cycle)","notes":"Digital gold · institutional reserve",                "target_2x":"~$252,000"},
    {"ticker":"ETH",     "name":"Ethereum",                                   "batch":"2x ATH",       "category":"Likely",           "price_jun26":"~$1,570",     "ath":"~$4,950",      "pct_to_ath":"-68%",   "verdict":"Likely (bull cycle)","notes":"L1 · staking / institutional ETF",                    "target_2x":"~$9,900"},
    {"ticker":"BNB",     "name":"BNB",                                        "batch":"2x ATH",       "category":"Likely",           "price_jun26":"~$567",       "ath":"~$850",        "pct_to_ath":"-33%",   "verdict":"Likely (bull cycle)","notes":"Binance token · exchange + chain utility",            "target_2x":"~$1,700"},
    {"ticker":"XRP",     "name":"XRP",                                        "batch":"2x ATH",       "category":"Likely",           "price_jun26":"~$1.05",      "ath":"~$3.66",       "pct_to_ath":"-71%",   "verdict":"Likely (bull cycle)","notes":"Ripple payments · ETF launched",                      "target_2x":"~$7.32"},
    # Possible
    {"ticker":"TRX",     "name":"Tron",                                       "batch":"2x ATH",       "category":"Possible",         "price_jun26":"~$0.32",      "ath":"~$0.45",       "pct_to_ath":"-29%",   "verdict":"Possible",         "notes":"Stablecoin volume · Justin Sun network",              "target_2x":"~$0.90"},
    {"ticker":"LEO",     "name":"UNUS SED LEO",                               "batch":"2x ATH",       "category":"Possible",         "price_jun26":"~$9.30",      "ath":"~$11",         "pct_to_ath":"-15%",   "verdict":"Possible",         "notes":"Bitfinex · buyback model",                            "target_2x":"~$22"},
    {"ticker":"XLM",     "name":"Stellar",                                    "batch":"2x ATH",       "category":"Possible",         "price_jun26":"~$0.19",      "ath":"~$0.65",       "pct_to_ath":"-71%",   "verdict":"Possible",         "notes":"Payments · DTCC designation pending",                 "target_2x":"~$1.30"},
    {"ticker":"LTC",     "name":"Litecoin",                                   "batch":"2x ATH",       "category":"Possible",         "price_jun26":"~$42",        "ath":"~$110",        "pct_to_ath":"-62%",   "verdict":"Possible",         "notes":"Payments OG · fading relevance",                      "target_2x":"~$220"},
    {"ticker":"TAO",     "name":"Bittensor",                                  "batch":"2x ATH",       "category":"Possible",         "price_jun26":"~$270",       "ath":"~$650",        "pct_to_ath":"-58%",   "verdict":"Possible",         "notes":"AI + decentralised ML",                               "target_2x":"~$1,300"},
    {"ticker":"UNI",     "name":"Uniswap",                                    "batch":"2x ATH",       "category":"Possible",         "price_jun26":"~$6.50",      "ath":"~$18",         "pct_to_ath":"-64%",   "verdict":"Possible",         "notes":"DEX governance · fee switch debate",                  "target_2x":"~$36"},
    {"ticker":"QNT",     "name":"Quant",                                      "batch":"2x ATH",       "category":"Possible",         "price_jun26":"~$65",        "ath":"~$130",        "pct_to_ath":"-50%",   "verdict":"Possible",         "notes":"Enterprise interop · niche but loyal",                "target_2x":"~$260"},
    {"ticker":"NEXO",    "name":"Nexo",                                       "batch":"2x ATH",       "category":"Possible",         "price_jun26":"~$1.20",      "ath":"~$2.50",       "pct_to_ath":"-52%",   "verdict":"Possible",         "notes":"Crypto lending · buyback model",                      "target_2x":"~$5.00"},
    {"ticker":"SKY",     "name":"Sky (MakerDAO)",                             "batch":"2x ATH",       "category":"Possible",         "price_jun26":"~$0.14",      "ath":"~$0.28",       "pct_to_ath":"-50%",   "verdict":"Possible",         "notes":"MakerDAO rebranded · DAI ecosystem",                  "target_2x":"~$0.56"},
    {"ticker":"MORPHO",  "name":"Morpho",                                     "batch":"2x ATH",       "category":"Possible",         "price_jun26":"~$0.90",      "ath":"~$3.50",       "pct_to_ath":"-74%",   "verdict":"Possible",         "notes":"DeFi lending · growing TVL",                          "target_2x":"~$7.00"},
    {"ticker":"WBT",     "name":"WhiteBIT Token",                             "batch":"2x ATH",       "category":"Possible",         "price_jun26":"~$22",        "ath":"~$30",         "pct_to_ath":"-27%",   "verdict":"Possible",         "notes":"WhiteBIT exchange token",                             "target_2x":"~$60"},
    # Unlikely
    {"ticker":"DEXE",    "name":"DeXe",                                       "batch":"2x ATH",       "category":"Unlikely",         "price_jun26":"~$5",         "ath":"~$20",         "pct_to_ath":"-75%",   "verdict":"Unlikely",         "notes":"DAO tooling · niche governance",                      "target_2x":"~$40"},
    {"ticker":"KCS",     "name":"KuCoin Token",                               "batch":"2x ATH",       "category":"Unlikely",         "price_jun26":"~$6",         "ath":"~$14",         "pct_to_ath":"-57%",   "verdict":"Unlikely",         "notes":"KuCoin exchange token · regulatory uncertainty",      "target_2x":"~$28"},
    {"ticker":"GT",      "name":"Gate Token",                                 "batch":"2x ATH",       "category":"Unlikely",         "price_jun26":"~$8",         "ath":"~$24",         "pct_to_ath":"-67%",   "verdict":"Unlikely",         "notes":"Gate.io token · shrinking EU exposure",               "target_2x":"~$48"},
    {"ticker":"HTX",     "name":"HTX",                                        "batch":"2x ATH",       "category":"Unlikely",         "price_jun26":"~$3.50",      "ath":"~$7",          "pct_to_ath":"-50%",   "verdict":"Unlikely",         "notes":"HTX (formerly Huobi) · regulatory issues",           "target_2x":"~$14"},
    {"ticker":"XDC",     "name":"XDC Network",                                "batch":"2x ATH",       "category":"Unlikely",         "price_jun26":"~$0.045",     "ath":"~$0.12",       "pct_to_ath":"-62%",   "verdict":"Unlikely",         "notes":"Trade finance · obscure",                             "target_2x":"~$0.24"},
    {"ticker":"JST",     "name":"JUST",                                       "batch":"2x ATH",       "category":"Unlikely",         "price_jun26":"~$0.021",     "ath":"~$0.055",      "pct_to_ath":"-62%",   "verdict":"Unlikely",         "notes":"Tron DeFi · low demand outside ecosystem",           "target_2x":"~$0.11"},
    {"ticker":"VVV",     "name":"Venice Finance",                             "batch":"2x ATH",       "category":"Unlikely",         "price_jun26":"~$2.50",      "ath":"~$18",         "pct_to_ath":"-86%",   "verdict":"Unlikely",         "notes":"AI privacy · micro-cap"},
]

# Verdict order for sorting
VERDICT_ORDER = {
    "Already exceeded ATH": 0,
    "Already near ATH": 1,
    "Likely (bull cycle)": 2,
    "Likely": 2,
    "Possible": 3,
    "Unlikely": 4,
    "No data": 5,
}
```

---

## Step 2 — Add the render function

Add this function in app.py, after render_analyser_tab() and before main():

```python
def render_ath_tracker_tab():
    st.markdown("## ATH recovery tracker")
    st.markdown(
        "All assets from the Jun 26 2026 ATH analysis. "
        "Post-Oct 2025 cycle high used as ATH reference unless noted. "
        "Data as of June 26, 2026."
    )

    # ── Filters ──────────────────────────────────────────────────────────────
    f1, f2, f3 = st.columns([2, 2, 2])
    with f1:
        batch_filter = st.selectbox(
            "Batch",
            ["All", "Major Alts", "L1s & DeFi", "Meme Coins", "2x ATH"],
            label_visibility="visible",
        )
    with f2:
        verdict_filter = st.multiselect(
            "Verdict",
            ["Already exceeded ATH", "Already near ATH", "Likely (bull cycle)",
             "Likely", "Possible", "Unlikely"],
            default=["Already exceeded ATH", "Already near ATH",
                     "Likely (bull cycle)", "Likely", "Possible"],
        )
    with f3:
        search_q = st.text_input("Search ticker or name", placeholder="e.g. SOL")

    # ── Filter data ───────────────────────────────────────────────────────────
    rows = ATH_DATA
    if batch_filter != "All":
        rows = [r for r in rows if r["batch"] == batch_filter]
    if verdict_filter:
        rows = [r for r in rows if r["verdict"] in verdict_filter]
    if search_q.strip():
        q = search_q.strip().upper()
        rows = [r for r in rows
                if q in r["ticker"].upper() or q in r["name"].upper()]

    # Sort by verdict priority then ticker
    rows = sorted(rows, key=lambda r: (VERDICT_ORDER.get(r["verdict"], 9), r["ticker"]))

    # ── Summary metrics ───────────────────────────────────────────────────────
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Total shown", len(rows))
    m2.metric("Already at/exceeded ATH",
              sum(1 for r in rows if "exceeded" in r["verdict"].lower()
                  or "near" in r["verdict"].lower()))
    m3.metric("Likely",
              sum(1 for r in rows if "likely" in r["verdict"].lower()))
    m4.metric("Possible",
              sum(1 for r in rows if r["verdict"] == "Possible"))
    m5.metric("Unlikely",
              sum(1 for r in rows if r["verdict"] == "Unlikely"))

    st.markdown("---")

    # ── Verdict color map ─────────────────────────────────────────────────────
    VERDICT_STYLE = {
        "Already exceeded ATH": ("#d1fae5", "#065f46", "⬆"),
        "Already near ATH":     ("#d1fae5", "#065f46", "✅"),
        "Likely (bull cycle)":  ("#dcfce7", "#166534", "🟢"),
        "Likely":               ("#dcfce7", "#166534", "🟢"),
        "Possible":             ("#fef3c7", "#92400e", "🟡"),
        "Unlikely":             ("#fee2e2", "#991b1b", "🔴"),
        "No data":              ("#f1f5f9", "#64748b", "⬛"),
    }

    # ── Table ─────────────────────────────────────────────────────────────────
    # Header
    hcols = st.columns([1, 2.5, 1.2, 1.2, 1.2, 1.5, 3])
    for col, label in zip(hcols, ["Ticker", "Name", "Price Jun 26", "ATH", "% to ATH", "Verdict", "Notes"]):
        col.markdown(
            f"<div style='font-size:0.72rem;font-weight:700;letter-spacing:0.05em;"
            f"text-transform:uppercase;color:#94a3b8'>{label}</div>",
            unsafe_allow_html=True
        )

    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

    for row in rows:
        bg, fg, icon = VERDICT_STYLE.get(row["verdict"], ("#f1f5f9", "#64748b", "⬛"))
        c1, c2, c3, c4, c5, c6, c7 = st.columns([1, 2.5, 1.2, 1.2, 1.2, 1.5, 3])

        with c1:
            st.markdown(
                f"<div style='font-weight:700;color:#1e293b;font-size:0.85rem;"
                f"padding:4px 0'>{row['ticker']}</div>",
                unsafe_allow_html=True
            )
        with c2:
            st.markdown(
                f"<div style='color:#475569;font-size:0.82rem;padding:4px 0'>"
                f"{row['name']}</div>",
                unsafe_allow_html=True
            )
        with c3:
            st.markdown(
                f"<div style='color:#1e293b;font-size:0.82rem;padding:4px 0'>"
                f"{row['price_jun26']}</div>",
                unsafe_allow_html=True
            )
        with c4:
            st.markdown(
                f"<div style='color:#1e293b;font-size:0.82rem;padding:4px 0'>"
                f"{row['ath']}</div>",
                unsafe_allow_html=True
            )
        with c5:
            pct = row['pct_to_ath']
            color = "#16a34a" if pct.startswith("+") else "#dc2626" if pct.startswith("-") else "#64748b"
            st.markdown(
                f"<div style='color:{color};font-weight:600;font-size:0.82rem;padding:4px 0'>"
                f"{pct}</div>",
                unsafe_allow_html=True
            )
        with c6:
            st.markdown(
                f"<div style='background:{bg};color:{fg};font-size:0.72rem;font-weight:600;"
                f"padding:3px 8px;border-radius:10px;display:inline-block;margin-top:2px'>"
                f"{icon} {row['verdict']}</div>",
                unsafe_allow_html=True
            )
        with c7:
            # Show 2x target for Batch 4 entries that have it
            extra = ""
            if row.get("target_2x"):
                extra = f" · <strong>2x target: {row['target_2x']}</strong>"
            st.markdown(
                f"<div style='color:#64748b;font-size:0.78rem;padding:4px 0'>"
                f"{row['notes']}{extra}</div>",
                unsafe_allow_html=True
            )

        # Divider
        st.markdown(
            "<div style='height:1px;background:#f1f5f9;margin:1px 0'></div>",
            unsafe_allow_html=True
        )

    if not rows:
        st.info("No assets match the current filters.")

    # ── Legend ────────────────────────────────────────────────────────────────
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
        unsafe_allow_html=True
    )
```

---

## Step 3 — Wire into main()

In main(), find the tabs line and update it:

```python
    tab1, tab2, tab3 = st.tabs([
        "📖 Methodology and framework",
        "🔍 Analyse a coin",
        "📊 ATH Tracker"
    ])

    with tab1:
        render_methodology_tab()
    with tab2:
        render_analyser_tab()
    with tab3:
        render_ath_tracker_tab()
```

If the live feed tab from the DexScreener pipeline work has already been added,
update to 4 tabs instead:

```python
    tab1, tab2, tab3, tab4 = st.tabs([
        "📖 Methodology and framework",
        "🔍 Analyse a coin",
        "📡 Live feed",
        "📊 ATH Tracker"
    ])

    with tab1:
        render_methodology_tab()
    with tab2:
        render_analyser_tab()
    with tab3:
        render_live_feed_tab()
    with tab4:
        render_ath_tracker_tab()
```

---

## What this adds

- 76 assets across 4 batches with full verdict, price, ATH, % gap, and notes
- Stablecoins, T-bills, and ambiguous tickers excluded — actionable assets only
- 5 summary metric cards (total, exceeded, likely, possible, unlikely)
- Batch filter, multi-select verdict filter, and live ticker/name search
- Colour-coded verdict pills and green/red % to ATH
- 2x ATH targets shown inline for Batch 4 assets
- Legend strip at the bottom
- No external file dependency — all data hardcoded from the xlsx

## Things to preserve

- Do not modify SYSTEM_PROMPT, make_anthropic_client(), get_api_key(), or get_verdict()
- Keep ATH_DATA and VERDICT_ORDER additions near the top constants block
- render_ath_tracker_tab() is self-contained — no new imports needed
