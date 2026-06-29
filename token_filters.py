"""Shared token exclusion rules (stablecoins, ATH commodities)."""

from __future__ import annotations

STABLECOIN_SYMBOLS = {
    "USDT", "USDC", "DAI", "USDE", "FDUSD", "TUSD", "USDD", "PYUSD", "USDS",
    "FRAX", "LUSD", "CRVUSD", "GUSD", "BUSD", "EURC", "USD1", "USDT0", "USD0",
    "USDBC", "USDG", "USDP", "SUSD", "MIM", "DOLA", "USDX", "UST", "USTC",
    "EURS", "EURT", "AEUR", "CUSD", "HUSD", "USDK", "USDN", "USDR", "USX",
    "ALUSD", "MUSD", "OUSD", "RSV", "USN", "XUSD",
}

STABLECOIN_COINGECKO_IDS = {
    "tether", "usd-coin", "dai", "ethena-usde", "first-digital-usd",
    "true-usd", "paypal-usd", "frax", "liquity-usd", "gemini-dollar",
    "binance-usd", "paxos-standard", "pax-dollar", "crvusd", "usdd",
    "usds", "euro-coin", "usd1-wlfi", "usdt0", "usd0-liquid-utility-token",
    "usdb", "usdg", "stasis-eurs", "celo-dollar", "nusd", "origin-dollar",
    "magic-internet-money", "dola-usd", "liquity-usd", "susd", "husd",
}

STABLECOIN_NAME_HINTS = (
    "stablecoin",
    "usd stable",
    "wrapped usd",
    "tether",
    "usd coin",
    "paypal usd",
)

# Gold / index tokens excluded from ATH batches only (not memecoin pipeline).
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


def is_ath_excluded(
    symbol: str | None = None,
    name: str | None = None,
    coingecko_id: str | None = None,
) -> bool:
    sym = (symbol or "").strip().upper()
    if sym in COMMODITY_OR_INDEX_SYMBOLS:
        return True
    return is_stablecoin(symbol, name, coingecko_id)
