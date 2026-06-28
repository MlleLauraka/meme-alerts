#!/bin/bash
# Install weekly ATH refresh — Sundays 8:00 AM (before Monday pipeline report).
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
RUN_SCRIPT="$DIR/ath_run.sh"
LOG_FILE="$DIR/ath_run.log"
CRON_LINE="0 8 * * 0 $RUN_SCRIPT >> $LOG_FILE 2>&1"

chmod +x "$RUN_SCRIPT"

TMP="$(mktemp)"
crontab -l 2>/dev/null | grep -v "ath_run.sh" > "$TMP" || true
echo "$CRON_LINE" >> "$TMP"
crontab "$TMP"
rm "$TMP"

echo "Installed Sunday 8:00 AM ATH refresh cron:"
echo "  $CRON_LINE"
echo ""
echo "Logs: $LOG_FILE"
echo "Test now: $RUN_SCRIPT"
