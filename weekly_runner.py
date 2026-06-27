#!/usr/bin/env python3
"""Run the Monday weekly scan and append results to weekly_report.xlsx."""

import argparse
import sys

from dotenv import load_dotenv

from weekly_report import run_weekly_scan

load_dotenv()


def main() -> None:
    parser = argparse.ArgumentParser(description="Weekly memecoin pipeline report")
    parser.add_argument(
        "--date",
        help="Override report date (YYYY-MM-DD). Defaults to today.",
    )
    parser.add_argument(
        "--chains",
        default="",
        help="Comma-separated chains (default: all configured chains)",
    )
    args = parser.parse_args()

    chains = [c.strip() for c in args.chains.split(",") if c.strip()] or None

    try:
        results = run_weekly_scan(report_date=args.date, chains=chains)
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"Weekly scan complete — {len(results)} tokens scored and appended to weekly_report.xlsx")
    for r in sorted(results, key=lambda x: x["total"], reverse=True)[:10]:
        vetoed = r.get("vetoed", False)
        verdict = "DQ" if vetoed else f"{r['total']}/100"
        print(f"  {r['ticker']:8} {r['chain']:10} {verdict}")


if __name__ == "__main__":
    main()
