#!/usr/bin/env python3
"""Run the weekly ATH tracker refresh (top 100, batch rules, SQLite history)."""

import argparse
import sys

from dotenv import load_dotenv

from ath_refresh import run_ath_refresh

load_dotenv()


def main() -> None:
    parser = argparse.ArgumentParser(description="Weekly ATH tracker refresh")
    parser.add_argument(
        "--date",
        help="Snapshot date YYYY-MM-DD (default: today UTC)",
    )
    parser.add_argument(
        "--sleep",
        type=float,
        default=1.3,
        help="Seconds between CoinGecko history calls (default: 1.3)",
    )
    parser.add_argument(
        "--no-ai",
        action="store_true",
        help="Skip Claude verdict scoring (rule-based only)",
    )
    args = parser.parse_args()

    def progress(msg: str) -> None:
        print(msg)

    try:
        result = run_ath_refresh(
            snapshot_date=args.date,
            sleep_seconds=args.sleep,
            use_ai_verdicts=not args.no_ai,
            on_progress=progress,
        )
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

    print(
        f"ATH refresh complete — {result['count']} assets · "
        f"snapshot {result['snapshot_date']} · provider {result['provider']} · "
        f"verdicts {result.get('verdict_mode', 'rules')}"
    )
    if result.get("errors"):
        print(f"Warnings ({len(result['errors'])}):")
        for err in result["errors"][:10]:
            print(f"  - {err}")


if __name__ == "__main__":
    main()
