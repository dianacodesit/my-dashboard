#!/bin/bash
# NOTE: macOS LaunchAgents cannot read ~/Documents (TCC).
# The persistent GitHub board on :8081 is:
#   LaunchAgent  com.diana.my-dashboard-github-8081
#   Watchdog     /Users/diana/my-dashboard/keep-serve-github-8081.sh
#   Files        /Users/diana/github-my-dashboard  (sync of this checkout)
# Do not point LaunchAgent at this Documents path.
echo "Use LaunchAgent com.diana.my-dashboard-github-8081 → http://127.0.0.1:8081/" >&2
exit 0
