#!/bin/bash
# Run one job line "name|command" from $WORK/jobs.txt in the repository root.
# Skips jobs already marked done; logs to $WORK/logs/<name>.{log,done,fail}.
# Usage: tr '\n' '\0' < "$WORK/jobs.txt" | WORK="$WORK" xargs -0 -P 8 -n 1 scripts/parallel/run_job.sh
: "${WORK:?set WORK to the work directory used with make_jobs.py}"
REPO="$(cd "$(dirname "$0")/../.." && pwd)"
line="$1"; name="${line%%|*}"; cmd="${line#*|}"
LOGS="$WORK/logs"; mkdir -p "$LOGS"
[ -f "$LOGS/$name.done" ] && exit 0
rm -f "$LOGS/$name.fail"
start=$(date +%s)
if (cd "$REPO" && eval "$cmd") > "$LOGS/$name.log" 2>&1; then
  echo "$(( $(date +%s) - start ))s" > "$LOGS/$name.done"; echo "done $name ($(( $(date +%s) - start ))s)"
else
  touch "$LOGS/$name.fail"; echo "FAIL $name"
fi
