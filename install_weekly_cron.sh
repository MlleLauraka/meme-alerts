#!/bin/bash
# Install a crontab entry to run the weekly report every Monday at 9:00 AM.
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
RUN_SCRIPT="$DIR/weekly_run.sh"
LOG_FILE="$DIR/weekly_run.log"
CRON_LINE="0 9 * * 1 $RUN_SCRIPT >> $LOG_FILE 2>&1"

chmod +x "$RUN_SCRIPT"

TMP="$(mktemp)"
crontab -l 2>/dev/null | grep -v "weekly_run.sh" > "$TMP" || true
echo "$CRON_LINE" >> "$TMP"
crontab "$TMP"
rm "$TMP"

echo "Installed Monday 9:00 AM cron job:"
echo "  $CRON_LINE"
echo ""
echo "Logs: $LOG_FILE"
echo "Test now: $RUN_SCRIPT"
