"""Shared token exclusion rules (stablecoins, RWAs, ATH commodities)."""

from __future__ import annotations

STABLECOIN_SYMBOLS = {
    "USDT", "USDC", "DAI", "USDE", "FDUSD", "TUSD", "USDD", "PYUSD", "USDS",
    "FRAX", "LUSD", "CRVUSD", "GUSD", "BUSD", "EURC", "USD1", "USDT0", "USD0",
    "USDBC", "USDG", "USDP", "SUSD", "MIM", "DOLA", "USDX", "UST", "USTC",
    "EURS", "EURT", "AEUR", "CUSD", "HUSD", "USDK", "USDN", "USDR", "USX",
    "ALUSD", "MUSD", "OUSD", "RSV", "USN", "XUSD", "GHO", "USDF", "BFUSD",
    "USYC", "USDY", "USDTB", "USDGO", "STABLE",
}

STABLECOIN_COINGECKO_IDS = {
    "tether", "usd-coin", "dai", "ethena-usde", "first-digital-usd",
    "true-usd", "paypal-usd", "frax", "liquity-usd", "gemini-dollar",
    "binance-usd", "paxos-standard", "pax-dollar", "crvusd", "usdd",
    "usds", "euro-coin", "usd1-wlfi", "usdt0", "usd0-liquid-utility-token",
    "usdb", "usdg", "stasis-eurs", "celo-dollar", "nusd", "origin-dollar",
    "magic-internet-money", "dola-usd", "susd", "husd", "gho", "falcon-finance",
    "circle-usyc", "ondo-us-dollar-yield", "usd-tb", "usdgo",
}

STABLECOIN_NAME_HINTS = (
    "stablecoin",
    "usd stable",
    "wrapped usd",
    "tether",
    "usd coin",
    "paypal usd",
    "united stables",
)

# Tokenized treasuries, funds, credit, and other real-world assets.
RWA_SYMBOLS = {
    "JAAA", "USDF", "USYC", "BUIDL", "USDY", "BFUSD", "EUTBL", "STABLE",
    "USDGO", "USDTB", "GHO", "YLDS", "EURSAFO", "FIGR_HELOC", "BCAP",
    "OUSG", "USTB", "TBILL", "WSTUSR", "USCC", "STBT", "USDW", "USDZ",
}

RWA_COINGECKO_IDS = {
    "blackrock-usd-institutional-digital-liquidity-fund",
    "ondo-us-dollar-yield",
    "circle-usyc",
    "janus-henderson-anemoy-aaa-clo-fund",
    "spiko-eu-t-bills-money-market-fund",
    "spiko-amundi-overnight-swap-fund-eur",
    "figure-heloc",
    "blockchain-capital",
    "ylds",
    "falcon-finance",
    "gho",
    "usd-tb",
    "usdgo",
    "ousg",
    "superstate-short-duration-us-government-securities-fund-ustb",
    "openeden-tbill",
    "matrixdock-gold",
}

RWA_NAME_HINTS = (
    "real world asset",
    "tokenized treasur",
    "tokenised treasur",
    "treasury bill",
    "t-bill",
    "t-bills",
    "money market fund",
    "digital liquidity fund",
    "institutional digital",
    "us dollar yield",
    "clo fund",
    "heloc",
    "home equity",
    "overnight swap fund",
    "yield fund",
    "tokenized bond",
    "tokenised bond",
    "bond fund",
    "blackrock usd",
    "janus henderson",
    "spiko",
    "figure heloc",
    "falcon usd",
    "circle usyc",
    "government securities fund",
    "secured overnight",
    "private credit",
    "asset-backed",
    "asset backed",
    "tokenized us treasur",
    "tokenised us treasur",
    "treasury token",
    "treasury product",
)

# Gold / index tokens excluded from ATH batches only.
COMMODITY_OR_INDEX_SYMBOLS = {"PAXG", "XAUT", "SPX", "SPX6900"}


def is_stablecoin(
    symbol: str | None = None,
    name: str | None = None,
    coingecko_id: str | None = None,
) -> bool:
    sym = (symbol or "").strip().upper()
    if sym and sym in STABLECOIN_SYMBOLS:
        return True

    cid = (coingecko_id or "").strip().lower()
    if cid and cid in STABLECOIN_COINGECKO_IDS:
        return True

    nm = (name or "").strip().lower()
    if nm:
        for hint in STABLECOIN_NAME_HINTS:
            if hint in nm:
                return True

    return False


def is_rwa(
    symbol: str | None = None,
    name: str | None = None,
    coingecko_id: str | None = None,
) -> bool:
    sym = (symbol or "").strip().upper()
    nm = (name or "").strip().lower()

    if sym == "U" and "united stables" in nm:
        return True

    if sym and sym in RWA_SYMBOLS:
        return True

    cid = (coingecko_id or "").strip().lower()
    if cid and cid in RWA_COINGECKO_IDS:
        return True

    if nm:
        for hint in RWA_NAME_HINTS:
            if hint in nm:
                return True

    return False


def is_excluded_from_analysis(
    symbol: str | None = None,
    name: str | None = None,
    coingecko_id: str | None = None,
) -> bool:
    """Stablecoins and RWAs — skip memecoin pipeline / analyser / live feed."""
    return is_stablecoin(symbol, name, coingecko_id) or is_rwa(symbol, name, coingecko_id)


def is_ath_excluded(
    symbol: str | None = None,
    name: str | None = None,
    coingecko_id: str | None = None,
) -> bool:
    """Non-crypto assets excluded from ATH tracker batches."""
    sym = (symbol or "").strip().upper()
    if sym in COMMODITY_OR_INDEX_SYMBOLS:
        return True
    return is_excluded_from_analysis(symbol, name, coingecko_id)
