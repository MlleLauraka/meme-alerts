"""Chain explorer URLs and top-holder breakdown for the coin analyser."""

from __future__ import annotations

import os
import time
from typing import Any

import httpx

SOLANA_RPC = os.environ.get("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com")
ETHERSCAN_V2 = "https://api.etherscan.io/v2/api"
SOLSCAN_PRO = "https://pro-api.solscan.io/v2.0/token/holders"

# Etherscan API v2 chain IDs (one API key covers these explorers).
ETHERSCAN_CHAIN_IDS = {
    "ethereum": 1,
    "base": 8453,
    "bsc": 56,
    "arbitrum": 42161,
    "polygon": 137,
    "optimism": 10,
    "avax": 43114,
}

EXPLORER_META: dict[str, dict[str, str]] = {
    "solana": {"name": "Solscan", "base": "https://solscan.io"},
    "ethereum": {"name": "Etherscan", "base": "https://etherscan.io"},
    "base": {"name": "Basescan", "base": "https://basescan.org"},
    "bsc": {"name": "BscScan", "base": "https://bscscan.com"},
    "arbitrum": {"name": "Arbiscan", "base": "https://arbiscan.io"},
    "polygon": {"name": "Polygonscan", "base": "https://polygonscan.com"},
    "optimism": {"name": "Optimistic Etherscan", "base": "https://optimistic.etherscan.io"},
    "avax": {"name": "Snowtrace", "base": "https://snowtrace.io"},
}


def _http_client() -> httpx.Client:
    return httpx.Client(timeout=30.0, trust_env=False)


def _short_addr(addr: str, left: int = 6, right: int = 4) -> str:
    if not addr or len(addr) <= left + right + 3:
        return addr or "—"
    return f"{addr[:left]}…{addr[-right:]}"


def normalize_chain(chain_id: str) -> str:
    return (chain_id or "").strip().lower()


def get_explorer_links(chain_id: str, token_address: str) -> dict[str, str]:
    """Return labelled explorer URLs for a token mint/contract."""
    chain = normalize_chain(chain_id)
    addr = (token_address or "").strip()
    meta = EXPLORER_META.get(chain, {"name": "Explorer", "base": ""})
    base = meta["base"]

    if not base or not addr:
        return {
            "explorer_name": meta["name"],
            "token_url": "",
            "holders_url": "",
            "address_url": "",
        }

    if chain == "solana":
        token_url = f"{base}/token/{addr}"
        holders_url = f"{token_url}#holders"
        address_url = f"{base}/account/{addr}"
    else:
        token_url = f"{base}/token/{addr}"
        holders_url = f"{token_url}#balances"
        address_url = f"{base}/address/{addr}"

    return {
        "explorer_name": meta["name"],
        "token_url": token_url,
        "holders_url": holders_url,
        "address_url": address_url,
    }


def _account_explorer_url(chain: str, wallet: str) -> str:
    meta = EXPLORER_META.get(chain, {"base": ""})
    base = meta.get("base", "")
    if not base or not wallet:
        return ""
    if chain == "solana":
        return f"{base}/account/{wallet}"
    return f"{base}/address/{wallet}"


def _solana_rpc(method: str, params: list[Any]) -> Any:
    with _http_client() as client:
        for attempt in range(3):
            resp = client.post(
                SOLANA_RPC,
                json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params},
            )
            data = resp.json()
            if data.get("error", {}).get("code") == 429:
                time.sleep(1.5 * (attempt + 1))
                continue
            if data.get("error"):
                raise RuntimeError(data["error"].get("message", "Solana RPC error"))
            return data.get("result")
    raise RuntimeError("Solana RPC rate limit — try again or set SOLSCAN_API_KEY")


def _fetch_solana_holders_solscan(token_address: str, limit: int) -> list[dict[str, Any]]:
    api_key = os.environ.get("SOLSCAN_API_KEY", "").strip()
    if not api_key:
        return []

    with _http_client() as client:
        resp = client.get(
            SOLSCAN_PRO,
            params={"address": token_address, "page": 1, "page_size": min(limit, 40)},
            headers={"token": api_key, "accept": "application/json"},
        )
        if resp.status_code != 200:
            return []
        payload = resp.json()
        items = payload.get("data", {}).get("items") or payload.get("data") or []
        if not isinstance(items, list):
            return []

    holders: list[dict[str, Any]] = []
    for i, row in enumerate(items[:limit], start=1):
        wallet = row.get("owner") or row.get("address") or ""
        amount = float(row.get("amount") or row.get("ui_amount") or 0)
        pct = float(row.get("percentage") or row.get("percent") or 0)
        if pct <= 0 and amount > 0:
            pct = 0.0
        holders.append(
            {
                "rank": i,
                "address": wallet,
                "address_short": _short_addr(wallet),
                "amount": amount,
                "pct": pct,
                "explorer_url": _account_explorer_url("solana", wallet),
            }
        )
    return holders


def _fetch_solana_holders_rpc(token_address: str, limit: int) -> list[dict[str, Any]]:
    supply = _solana_rpc("getTokenSupply", [token_address])
    total_ui = float((supply or {}).get("value", {}).get("uiAmount") or 0)
    if total_ui <= 0:
        return []

    largest = _solana_rpc("getTokenLargestAccounts", [token_address])
    accounts = (largest or {}).get("value") or []
    if not accounts:
        return []

    token_accounts = [a["address"] for a in accounts[:limit]]
    parsed = _solana_rpc(
        "getMultipleAccounts",
        [token_accounts, {"encoding": "jsonParsed"}],
    )
    values = (parsed or {}).get("value") or []

    holders: list[dict[str, Any]] = []
    rank = 0
    for acct_meta, acct in zip(accounts[:limit], values):
        if not acct:
            continue
        info = (acct.get("data") or {}).get("parsed", {}).get("info", {})
        token_amount = info.get("tokenAmount") or {}
        ui_amount = float(token_amount.get("uiAmount") or 0)
        owner = info.get("owner") or acct_meta.get("address", "")
        if ui_amount <= 0:
            continue
        rank += 1
        pct = (ui_amount / total_ui) * 100 if total_ui else 0.0
        holders.append(
            {
                "rank": rank,
                "address": owner,
                "address_short": _short_addr(owner),
                "amount": ui_amount,
                "pct": pct,
                "explorer_url": _account_explorer_url("solana", owner),
            }
        )
    return holders


def _fetch_evm_total_supply(chain: str, token_address: str, api_key: str) -> float:
    chain_id = ETHERSCAN_CHAIN_IDS.get(chain)
    if not chain_id:
        return 0.0
    with _http_client() as client:
        resp = client.get(
            ETHERSCAN_V2,
            params={
                "chainid": chain_id,
                "module": "stats",
                "action": "tokensupply",
                "contractaddress": token_address,
                "apikey": api_key,
            },
        )
        data = resp.json()
        if data.get("status") != "1":
            return 0.0
        return float(data.get("result") or 0)


def _fetch_evm_holders(chain: str, token_address: str, limit: int) -> list[dict[str, Any]]:
    api_key = os.environ.get("ETHERSCAN_API_KEY", "").strip()
    chain_id = ETHERSCAN_CHAIN_IDS.get(chain)
    if not api_key or not chain_id:
        return []

    with _http_client() as client:
        resp = client.get(
            ETHERSCAN_V2,
            params={
                "chainid": chain_id,
                "module": "token",
                "action": "tokenholderlist",
                "contractaddress": token_address,
                "page": 1,
                "offset": min(limit, 50),
                "apikey": api_key,
            },
        )
        data = resp.json()
        if data.get("status") != "1":
            return []
        rows = data.get("result") or []
        if not isinstance(rows, list):
            return []

    total_supply = _fetch_evm_total_supply(chain, token_address, api_key)
    holders: list[dict[str, Any]] = []
    for i, row in enumerate(rows[:limit], start=1):
        wallet = row.get("TokenHolderAddress", "")
        qty_raw = int(row.get("TokenHolderQuantity", 0) or 0)
        if total_supply > 0:
            pct = (qty_raw / total_supply) * 100
        else:
            pct = 0.0
        holders.append(
            {
                "rank": i,
                "address": wallet,
                "address_short": _short_addr(wallet),
                "amount": qty_raw,
                "pct": pct,
                "explorer_url": _account_explorer_url(chain, wallet),
            }
        )
    return holders


def fetch_holder_breakdown(
    chain_id: str,
    token_address: str,
    *,
    limit: int = 10,
) -> dict[str, Any]:
    """Top holders with explorer links. Uses Solscan/Etherscan APIs or Solana RPC."""
    chain = normalize_chain(chain_id)
    addr = (token_address or "").strip()
    links = get_explorer_links(chain, addr)

    out: dict[str, Any] = {
        "chain": chain,
        "token_address": addr,
        "explorer": links,
        "holders": [],
        "top1_pct": 0.0,
        "top5_pct": 0.0,
        "top10_pct": 0.0,
        "source": "",
        "note": "",
    }

    if not chain or not addr:
        out["note"] = "No contract address available for holder lookup."
        return out

    holders: list[dict[str, Any]] = []
    try:
        if chain == "solana":
            holders = _fetch_solana_holders_solscan(addr, limit)
            if holders:
                out["source"] = "Solscan API"
            else:
                holders = _fetch_solana_holders_rpc(addr, limit)
                if holders:
                    out["source"] = "Solana RPC"
        elif chain in ETHERSCAN_CHAIN_IDS:
            holders = _fetch_evm_holders(chain, addr, limit)
            if holders:
                out["source"] = EXPLORER_META[chain]["name"]
    except Exception as exc:
        out["note"] = str(exc)

    if not holders:
        if chain == "solana":
            out["note"] = (
                "Could not load holders automatically (RPC rate limit). "
                "Open Solscan holders below, or add SOLSCAN_API_KEY to .env / Streamlit secrets."
            )
        elif chain in ETHERSCAN_CHAIN_IDS:
            out["note"] = (
                f"Add ETHERSCAN_API_KEY (free at etherscan.io) to load top holders for "
                f"{EXPLORER_META[chain]['name']}."
            )
        else:
            out["note"] = f"No automatic holder API for {chain}. Use the explorer link below."

    out["holders"] = holders
    if holders:
        pcts = [h["pct"] for h in holders]
        out["top1_pct"] = pcts[0]
        out["top5_pct"] = sum(pcts[:5])
        out["top10_pct"] = sum(pcts[:10])

    return out
