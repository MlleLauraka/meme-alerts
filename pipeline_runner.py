#!/usr/bin/env python3
import argparse
import time

from dotenv import load_dotenv

from pipeline import (
    CHAINS,
    PIPELINE_SCORE_THRESHOLD,
    POLL_INTERVAL_SECS,
    DexPair,
    fetch_dex_pairs,
    get_api_key_from_env,
    log_candidate,
    pre_filter,
    quant_score,
    score_coin_hybrid,
)

load_dotenv()


def process_pair(pair: DexPair, api_key: str, threshold: int) -> None:
    passed, reason = pre_filter(pair)
    if not passed:
        print(f"SKIP {pair.token_symbol} ({pair.chain_id}): {reason}")
        return

    quant = quant_score(pair)
    result = score_coin_hybrid(pair, quant, api_key=api_key)
    if result is None:
        print(f"FAIL {pair.token_symbol} ({pair.chain_id}): API error")
        return

    if result["total"] >= threshold:
        logged = log_candidate(result)
        status = "LOGGED" if logged else "DUPE"
        print(f"{status} {pair.token_symbol} ({pair.chain_id}): {result['total']}/100")
    else:
        print(
            f"LOW {pair.token_symbol} ({pair.chain_id}): "
            f"{result['total']}/100 below threshold {threshold}"
        )


def scan_chains(chains: list[str], api_key: str, threshold: int, seen: set[str] | None = None) -> None:
    for chain in chains:
        pairs = fetch_dex_pairs(chain)
        print(f"Chain {chain}: {len(pairs)} pairs fetched")
        for pair in pairs:
            if seen is not None:
                if pair.pair_address in seen:
                    continue
                seen.add(pair.pair_address)
            process_pair(pair, api_key, threshold)


def main() -> None:
    parser = argparse.ArgumentParser(description="DexScreener pipeline runner")
    parser.add_argument("--mode", choices=["poll", "stream"], default="poll")
    parser.add_argument("--chains", default=",".join(CHAINS), help="Comma-separated chain list")
    parser.add_argument("--threshold", type=int, default=PIPELINE_SCORE_THRESHOLD)
    args = parser.parse_args()

    chains = [c.strip() for c in args.chains.split(",") if c.strip()]
    api_key = get_api_key_from_env()
    if not api_key:
        raise SystemExit("ANTHROPIC_API_KEY not set. Add it to .env or your environment.")

    seen: set[str] = set()
    sleep_secs = POLL_INTERVAL_SECS if args.mode == "poll" else 30

    print(f"Starting {args.mode} mode on chains: {', '.join(chains)}")
    try:
        while True:
            scan_chains(chains, api_key, args.threshold, seen=seen if args.mode == "stream" else None)
            print(f"Sleeping {sleep_secs}s...")
            time.sleep(sleep_secs)
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
