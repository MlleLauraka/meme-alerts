# ATH Tracker data (source: Crypto_ATH_Analysis_Jun2026.xlsx)
ATH_DATA = [
    # Batch 1 — Top 100 3x-5x
    # Already at / near ATH
    {"ticker":"SPX",     "name":"S&P 500 Index",                              "batch":"Top 100 3x-5x",    "category":"Already near ATH", "price_jun26":"$7,350",      "ath":"$7,621",       "pct_to_ath":"-3.5%",  "verdict":"Already near ATH", "notes":"S&P 500 Index"},
    # Likely
    {"ticker":"SOL",     "name":"Solana",                                     "batch":"Top 100 3x-5x",    "category":"Likely",           "price_jun26":"~$70",        "ath":"~$295",        "pct_to_ath":"-76%",   "verdict":"Likely",           "notes":"Layer 1 · High utility · ETF / treasury adoption"},
    {"ticker":"LINK",    "name":"Chainlink",                                  "batch":"Top 100 3x-5x",    "category":"Likely",           "price_jun26":"~$7.30",      "ath":"~$14",         "pct_to_ath":"-48%",   "verdict":"Likely",           "notes":"Oracle infra · 47-bank RWA settlement · 2x target"},
    {"ticker":"AAVE",    "name":"Aave",                                       "batch":"Top 100 3x-5x",    "category":"Likely",           "price_jun26":"~$140",       "ath":"~$340",        "pct_to_ath":"-59%",   "verdict":"Likely",           "notes":"DeFi lending · Kraken 15% stake talks"},
    {"ticker":"OKB",     "name":"OKB",                                        "batch":"Top 100 3x-5x",    "category":"Likely",           "price_jun26":"~$38",        "ath":"~$65",         "pct_to_ath":"-42%",   "verdict":"Likely",           "notes":"OKX exchange token · buy-burn"},
    {"ticker":"ONDO",    "name":"Ondo Finance",                               "batch":"Top 100 3x-5x",    "category":"Likely",           "price_jun26":"~$0.36",      "ath":"~$0.90",       "pct_to_ath":"-60%",   "verdict":"Likely",           "notes":"RWA tokenization leader"},
    {"ticker":"BGB",     "name":"Bitget Token",                               "batch":"Top 100 3x-5x",    "category":"Likely",           "price_jun26":"~$3.80",      "ath":"~$9.00",       "pct_to_ath":"-58%",   "verdict":"Likely",           "notes":"Bitget exchange token"},
    # Possible
    {"ticker":"DOGE",    "name":"Dogecoin",                                   "batch":"Top 100 3x-5x",    "category":"Possible",         "price_jun26":"~$0.10",      "ath":"~$0.48",       "pct_to_ath":"-79%",   "verdict":"Possible",         "notes":"OG meme / payments · Elon factor"},
    {"ticker":"HBAR",    "name":"Hedera",                                     "batch":"Top 100 3x-5x",    "category":"Possible",         "price_jun26":"~$0.078",     "ath":"~$0.40",       "pct_to_ath":"-80%",   "verdict":"Possible",         "notes":"Enterprise DLT · ETF approved"},
    {"ticker":"BCH",     "name":"Bitcoin Cash",                               "batch":"Top 100 3x-5x",    "category":"Possible",         "price_jun26":"~$380",       "ath":"~$800",        "pct_to_ath":"-52%",   "verdict":"Possible",         "notes":"Payments fork · fading relevance"},
    {"ticker":"PEPE",    "name":"Pepe",                                       "batch":"Top 100 3x-5x",    "category":"Possible",         "price_jun26":"~$0.0000070", "ath":"~$0.000027",   "pct_to_ath":"-74%",   "verdict":"Possible",         "notes":"Top meme by volume · cultural staying power"},
    {"ticker":"AVAX",    "name":"Avalanche",                                  "batch":"Top 100 3x-5x",    "category":"Possible",         "price_jun26":"~$6.50",      "ath":"~$45",         "pct_to_ath":"-86%",   "verdict":"Possible",         "notes":"Layer 1 · Subnet ecosystem"},
    {"ticker":"FET",     "name":"Fetch.ai",                                   "batch":"Top 100 3x-5x",    "category":"Possible",         "price_jun26":"~$0.50",      "ath":"~$3.40",       "pct_to_ath":"-85%",   "verdict":"Possible",         "notes":"AI agents · ASI Alliance"},
    {"ticker":"CRO",     "name":"Cronos",                                     "batch":"Top 100 3x-5x",    "category":"Possible",         "price_jun26":"~$0.070",     "ath":"~$0.22",       "pct_to_ath":"-68%",   "verdict":"Possible",         "notes":"Crypto.com ecosystem · consumer"},
    {"ticker":"SHIB",    "name":"Shiba Inu",                                  "batch":"Top 100 3x-5x",    "category":"Possible",         "price_jun26":"~$0.0000050", "ath":"~$0.000015",   "pct_to_ath":"-67%",   "verdict":"Possible",         "notes":"Shibarium L2 · large community"},
    {"ticker":"TIA",     "name":"Celestia",                                   "batch":"Top 100 3x-5x",    "category":"Possible",         "price_jun26":"~$1.80",      "ath":"~$8.00",       "pct_to_ath":"-77%",   "verdict":"Possible",         "notes":"Modular DA layer"},
    {"ticker":"POL",     "name":"Polygon (rebranded)",                        "batch":"Top 100 3x-5x",    "category":"Possible",         "price_jun26":"~$0.19",      "ath":"~$0.72",       "pct_to_ath":"-74%",   "verdict":"Possible",         "notes":"Polygon rebranded · L2 infra"},
    {"ticker":"ASTER",   "name":"Astar",                                      "batch":"Top 100 3x-5x",    "category":"Possible",         "price_jun26":"~$0.12",      "ath":"~$0.50",       "pct_to_ath":"-76%",   "verdict":"Possible",         "notes":"AI infra / compute"},
    {"ticker":"FIL",     "name":"Filecoin",                                   "batch":"Top 100 3x-5x",    "category":"Possible",         "price_jun26":"~$2.20",      "ath":"~$8.00",       "pct_to_ath":"-72%",   "verdict":"Possible",         "notes":"Decentralized storage"},
    # Unlikely
    {"ticker":"FLR",     "name":"Flare",                                      "batch":"Top 100 3x-5x",    "category":"Unlikely",         "price_jun26":"~$0.012",     "ath":"~$0.058",      "pct_to_ath":"-79%",   "verdict":"Unlikely",         "notes":"Cross-chain oracle · weak demand"},
    {"ticker":"TRUMP",   "name":"Official Trump",                             "batch":"Top 100 3x-5x",    "category":"Unlikely",         "price_jun26":"~$1.68",      "ath":"~$74",         "pct_to_ath":"-98%",   "verdict":"Unlikely",         "notes":"Meme/political · -98% · token unlocks · insider losses"},
    {"ticker":"WLFI",    "name":"World Liberty Financial",                    "batch":"Top 100 3x-5x",    "category":"Unlikely",         "price_jun26":"~$0.11",      "ath":"~$0.18",       "pct_to_ath":"-39%",   "verdict":"Unlikely",         "notes":"DeFi / Trump-linked governance · illiquid"},
    {"ticker":"PUMP",    "name":"Pump.fun",                                   "batch":"Top 100 3x-5x",    "category":"Unlikely",         "price_jun26":"~$0.003",     "ath":"~$0.016",      "pct_to_ath":"-81%",   "verdict":"Unlikely",         "notes":"pump.fun token · launchpad hype cooled"},
    {"ticker":"SPX6900", "name":"SPX6900",                                    "batch":"Top 100 3x-5x",    "category":"Unlikely",         "price_jun26":"~$0.33",      "ath":"~$2.27",       "pct_to_ath":"-85%",   "verdict":"Unlikely",         "notes":"Meme coin · community thin"},

    # Batch 2 — Top 100 >5x
    # Possible
    {"ticker":"SUI",     "name":"Sui",                                        "batch":"Top 100 >5x",   "category":"Possible",         "price_jun26":"~$0.69",      "ath":"~$5.35",       "pct_to_ath":"-87%",   "verdict":"Possible",         "notes":"L1 · Strong ecosystem · Cetus hack overhang"},
    {"ticker":"ENA",     "name":"Ethena",                                     "batch":"Top 100 >5x",   "category":"Possible",         "price_jun26":"~$0.08",      "ath":"~$0.50",       "pct_to_ath":"-84%",   "verdict":"Possible",         "notes":"Synthetic dollar · fee switch · unlock pressure"},
    {"ticker":"ADA",     "name":"Cardano",                                    "batch":"Top 100 >5x",   "category":"Possible",         "price_jun26":"~$0.147",     "ath":"~$1.25",       "pct_to_ath":"-88%",   "verdict":"Possible",         "notes":"L1 · Large supply · fading narrative"},
    {"ticker":"VET",     "name":"VeChain",                                    "batch":"Top 100 >5x",   "category":"Possible",         "price_jun26":"~$0.016",     "ath":"~$0.055",      "pct_to_ath":"-71%",   "verdict":"Possible",         "notes":"Enterprise supply chain · low traction"},
    {"ticker":"MNT",     "name":"Mantle",                                     "batch":"Top 100 >5x",   "category":"Possible",         "price_jun26":"~$0.45",      "ath":"~$1.40",       "pct_to_ath":"-68%",   "verdict":"Possible",         "notes":"Mantle L2 · Bybit-backed · shrinking TVL"},
    {"ticker":"ETHFI",   "name":"Ether.fi",                                   "batch":"Top 100 >5x",   "category":"Possible",         "price_jun26":"~$0.37",      "ath":"~$3.00",       "pct_to_ath":"-88%",   "verdict":"Possible",         "notes":"Liquid restaking · niche DeFi"},
    # Unlikely
    {"ticker":"APT",     "name":"Aptos",                                      "batch":"Top 100 >5x",   "category":"Unlikely",         "price_jun26":"~$0.58",      "ath":"~$13.91",      "pct_to_ath":"-96%",   "verdict":"Unlikely",         "notes":"L1 · supply inflation · lost to SUI"},
    {"ticker":"ARB",     "name":"Arbitrum",                                   "batch":"Top 100 >5x",   "category":"Unlikely",         "price_jun26":"~$0.076",     "ath":"~$0.72",       "pct_to_ath":"-89%",   "verdict":"Unlikely",         "notes":"L2 governance token · no fee accrual"},
    {"ticker":"SEI",     "name":"Sei",                                        "batch":"Top 100 >5x",   "category":"Unlikely",         "price_jun26":"~$0.050",     "ath":"~$0.60",       "pct_to_ath":"-92%",   "verdict":"Unlikely",         "notes":"L1 · exchange chain · struggling traction"},
    {"ticker":"DOT",     "name":"Polkadot",                                   "batch":"Top 100 >5x",   "category":"Unlikely",         "price_jun26":"~$0.85",      "ath":"~$7.98",       "pct_to_ath":"-89%",   "verdict":"Unlikely",         "notes":"L0 · lost developer mindshare · near ATL"},
    {"ticker":"PENGU",   "name":"Pudgy Penguins",                             "batch":"Top 100 >5x",   "category":"Unlikely",         "price_jun26":"~$0.006",     "ath":"~$0.048",      "pct_to_ath":"-88%",   "verdict":"Unlikely",         "notes":"NFT meme token · no utility catalyst"},
    {"ticker":"BONK",    "name":"Bonk",                                       "batch":"Top 100 >5x",   "category":"Unlikely",         "price_jun26":"~$0.0000090", "ath":"~$0.000060",   "pct_to_ath":"-85%",   "verdict":"Unlikely",         "notes":"Solana OG meme · hype cycle exhausted"},

    # Batch 3 — 2x +potential ATH
    # Already near / exceeded ATH
    {"ticker":"HYPE",    "name":"Hyperliquid",                                "batch":"2x +potential ATH",       "category":"Already near ATH", "price_jun26":"~$64",        "ath":"~$77",         "pct_to_ath":"n/a",    "verdict":"Already near ATH", "notes":"Hyperliquid · on-chain perps · just hit ATH ~$77",   "target_2x":"~$154"},
    {"ticker":"XMR",     "name":"Monero",                                     "batch":"2x +potential ATH",       "category":"Already exceeded", "price_jun26":"~$320",       "ath":"~$230",        "pct_to_ath":"+39%",   "verdict":"Already exceeded ATH","notes":"Monero · privacy · exceeded Oct '25 ATH",            "target_2x":"~$460"},
    {"ticker":"XAUT",    "name":"Tether Gold",                                "batch":"2x +potential ATH",       "category":"Already exceeded", "price_jun26":"~$3,340",     "ath":"~$2,650",      "pct_to_ath":"+26%",   "verdict":"Already exceeded ATH","notes":"Tether Gold · 1 troy oz gold",                        "target_2x":"~$5,300"},
    {"ticker":"PAXG",    "name":"Paxos Gold",                                 "batch":"2x +potential ATH",       "category":"Already exceeded", "price_jun26":"~$3,340",     "ath":"~$2,650",      "pct_to_ath":"+26%",   "verdict":"Already exceeded ATH","notes":"Paxos Gold",                                          "target_2x":"~$5,300"},
    {"ticker":"ZEC",     "name":"Zcash",                                      "batch":"2x +potential ATH",       "category":"Already exceeded", "price_jun26":"~$418",       "ath":"~$60",         "pct_to_ath":"+597%",  "verdict":"Already exceeded ATH","notes":"Zcash · privacy coin · well above Oct '25 level",     "target_2x":"~$120"},
    # Likely (bull cycle)
    {"ticker":"BTC",     "name":"Bitcoin",                                    "batch":"2x +potential ATH",       "category":"Likely",           "price_jun26":"~$60,000",    "ath":"~$126,000",    "pct_to_ath":"-52%",   "verdict":"Likely (bull cycle)","notes":"Digital gold · institutional reserve",                "target_2x":"~$252,000"},
    {"ticker":"ETH",     "name":"Ethereum",                                   "batch":"2x +potential ATH",       "category":"Likely",           "price_jun26":"~$1,570",     "ath":"~$4,950",      "pct_to_ath":"-68%",   "verdict":"Likely (bull cycle)","notes":"L1 · staking / institutional ETF",                    "target_2x":"~$9,900"},
    {"ticker":"BNB",     "name":"BNB",                                        "batch":"2x +potential ATH",       "category":"Likely",           "price_jun26":"~$567",       "ath":"~$850",        "pct_to_ath":"-33%",   "verdict":"Likely (bull cycle)","notes":"Binance token · exchange + chain utility",            "target_2x":"~$1,700"},
    {"ticker":"XRP",     "name":"XRP",                                        "batch":"2x +potential ATH",       "category":"Likely",           "price_jun26":"~$1.05",      "ath":"~$3.66",       "pct_to_ath":"-71%",   "verdict":"Likely (bull cycle)","notes":"Ripple payments · ETF launched",                      "target_2x":"~$7.32"},
    # Possible
    {"ticker":"TRX",     "name":"Tron",                                       "batch":"2x +potential ATH",       "category":"Possible",         "price_jun26":"~$0.32",      "ath":"~$0.45",       "pct_to_ath":"-29%",   "verdict":"Possible",         "notes":"Stablecoin volume · Justin Sun network",              "target_2x":"~$0.90"},
    {"ticker":"LEO",     "name":"UNUS SED LEO",                               "batch":"2x +potential ATH",       "category":"Possible",         "price_jun26":"~$9.30",      "ath":"~$11",         "pct_to_ath":"-15%",   "verdict":"Possible",         "notes":"Bitfinex · buyback model",                            "target_2x":"~$22"},
    {"ticker":"XLM",     "name":"Stellar",                                    "batch":"2x +potential ATH",       "category":"Possible",         "price_jun26":"~$0.19",      "ath":"~$0.65",       "pct_to_ath":"-71%",   "verdict":"Possible",         "notes":"Payments · DTCC designation pending",                 "target_2x":"~$1.30"},
    {"ticker":"LTC",     "name":"Litecoin",                                   "batch":"2x +potential ATH",       "category":"Possible",         "price_jun26":"~$42",        "ath":"~$110",        "pct_to_ath":"-62%",   "verdict":"Possible",         "notes":"Payments OG · fading relevance",                      "target_2x":"~$220"},
    {"ticker":"TAO",     "name":"Bittensor",                                  "batch":"2x +potential ATH",       "category":"Possible",         "price_jun26":"~$270",       "ath":"~$650",        "pct_to_ath":"-58%",   "verdict":"Possible",         "notes":"AI + decentralised ML",                               "target_2x":"~$1,300"},
    {"ticker":"UNI",     "name":"Uniswap",                                    "batch":"2x +potential ATH",       "category":"Possible",         "price_jun26":"~$6.50",      "ath":"~$18",         "pct_to_ath":"-64%",   "verdict":"Possible",         "notes":"DEX governance · fee switch debate",                  "target_2x":"~$36"},
    {"ticker":"QNT",     "name":"Quant",                                      "batch":"2x +potential ATH",       "category":"Possible",         "price_jun26":"~$65",        "ath":"~$130",        "pct_to_ath":"-50%",   "verdict":"Possible",         "notes":"Enterprise interop · niche but loyal",                "target_2x":"~$260"},
    {"ticker":"NEXO",    "name":"Nexo",                                       "batch":"2x +potential ATH",       "category":"Possible",         "price_jun26":"~$1.20",      "ath":"~$2.50",       "pct_to_ath":"-52%",   "verdict":"Possible",         "notes":"Crypto lending · buyback model",                      "target_2x":"~$5.00"},
    {"ticker":"SKY",     "name":"Sky (MakerDAO)",                             "batch":"2x +potential ATH",       "category":"Possible",         "price_jun26":"~$0.14",      "ath":"~$0.28",       "pct_to_ath":"-50%",   "verdict":"Possible",         "notes":"MakerDAO rebranded · DAI ecosystem",                  "target_2x":"~$0.56"},
    {"ticker":"MORPHO",  "name":"Morpho",                                     "batch":"2x +potential ATH",       "category":"Possible",         "price_jun26":"~$0.90",      "ath":"~$3.50",       "pct_to_ath":"-74%",   "verdict":"Possible",         "notes":"DeFi lending · growing TVL",                          "target_2x":"~$7.00"},
    {"ticker":"WBT",     "name":"WhiteBIT Token",                             "batch":"2x +potential ATH",       "category":"Possible",         "price_jun26":"~$22",        "ath":"~$30",         "pct_to_ath":"-27%",   "verdict":"Possible",         "notes":"WhiteBIT exchange token",                             "target_2x":"~$60"},
    # Unlikely
    {"ticker":"DEXE",    "name":"DeXe",                                       "batch":"2x +potential ATH",       "category":"Unlikely",         "price_jun26":"~$5",         "ath":"~$20",         "pct_to_ath":"-75%",   "verdict":"Unlikely",         "notes":"DAO tooling · niche governance",                      "target_2x":"~$40"},
    {"ticker":"KCS",     "name":"KuCoin Token",                               "batch":"2x +potential ATH",       "category":"Unlikely",         "price_jun26":"~$6",         "ath":"~$14",         "pct_to_ath":"-57%",   "verdict":"Unlikely",         "notes":"KuCoin exchange token · regulatory uncertainty",      "target_2x":"~$28"},
    {"ticker":"GT",      "name":"Gate Token",                                 "batch":"2x +potential ATH",       "category":"Unlikely",         "price_jun26":"~$8",         "ath":"~$24",         "pct_to_ath":"-67%",   "verdict":"Unlikely",         "notes":"Gate.io token · shrinking EU exposure",               "target_2x":"~$48"},
    {"ticker":"HTX",     "name":"HTX",                                        "batch":"2x +potential ATH",       "category":"Unlikely",         "price_jun26":"~$3.50",      "ath":"~$7",          "pct_to_ath":"-50%",   "verdict":"Unlikely",         "notes":"HTX (formerly Huobi) · regulatory issues",           "target_2x":"~$14"},
    {"ticker":"XDC",     "name":"XDC Network",                                "batch":"2x +potential ATH",       "category":"Unlikely",         "price_jun26":"~$0.045",     "ath":"~$0.12",       "pct_to_ath":"-62%",   "verdict":"Unlikely",         "notes":"Trade finance · obscure",                             "target_2x":"~$0.24"},
    {"ticker":"JST",     "name":"JUST",                                       "batch":"2x +potential ATH",       "category":"Unlikely",         "price_jun26":"~$0.021",     "ath":"~$0.055",      "pct_to_ath":"-62%",   "verdict":"Unlikely",         "notes":"Tron DeFi · low demand outside ecosystem",           "target_2x":"~$0.11"},
    {"ticker":"VVV",     "name":"Venice Finance",                             "batch":"2x +potential ATH",       "category":"Unlikely",         "price_jun26":"~$2.50",      "ath":"~$18",         "pct_to_ath":"-86%",   "verdict":"Unlikely",         "notes":"AI privacy · micro-cap"},
]

VERDICT_ORDER = {
    "Already exceeded ATH": 0,
    "Already near ATH": 1,
    "Likely (bull cycle)": 2,
    "Likely": 2,
    "Possible": 3,
    "Unlikely": 4,
    "No data": 5,
}

# Display order for the Batch filter (must match `batch` field on each row)
ATH_BATCHES = [
    "Top 100 3x-5x",
    "Top 100 >5x",
    "2x +potential ATH",
]

# Map old batch names (pre-rename) → current names
BATCH_LEGACY_ALIASES = {
    "Major Alts": "Top 100 3x-5x",
    "Top 100 3x><5x": "Top 100 3x-5x",
    "Top 100 3x<=5x": "Top 100 3x-5x",
    "L1s & DeFi": "Top 100 >5x",
    "2x ATH": "2x +potential ATH",
    "Meme Coins": None,
}


def normalize_batch_filter(value: str | None) -> str:
    """Resolve selectbox value to a valid batch filter ('All' or a current batch name)."""
    if not value or value == "All":
        return "All"
    if value in BATCH_LEGACY_ALIASES:
        mapped = BATCH_LEGACY_ALIASES[value]
        return mapped if mapped else "All"
    if value in ATH_BATCHES:
        return value
    return "All"
