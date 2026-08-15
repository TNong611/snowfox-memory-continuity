#!/bin/bash
# Gateway watchdog: SILENT unless a problem is found (cron no_agent mode)
# Checks: new gateway-crash entries, new TUI crash-log entries, backend process alive.
LOG_DIR="$HOME/AppData/Local/hermes/logs"
MARKER="$HOME/AppData/Local/hermes/scripts/.gw_watch_marker"
PROBLEM=""

# --- 1. new [gateway-crash] in desktop.log ---
if [ -f "$LOG_DIR/desktop.log" ]; then
  LINES=$(wc -l < "$LOG_DIR/desktop.log")
  PREV=0
  [ -f "$MARKER.desktop" ] && PREV=$(cat "$MARKER.desktop")
  if [ "$LINES" -gt "$PREV" ]; then
    NEW=$(sed -n "$((PREV+1)),${LINES}p" "$LOG_DIR/desktop.log" | grep -c "\[gateway-crash\]")
    [ "$NEW" -gt 0 ] && PROBLEM="${PROBLEM}desktop.log: ${NEW} new gateway-crash(s)\n"
  fi
  echo "$LINES" > "$MARKER.desktop"
fi

# --- 2. new thread exceptions in tui_gateway_crash.log ---
if [ -f "$LOG_DIR/tui_gateway_crash.log" ]; then
  LINES=$(wc -l < "$LOG_DIR/tui_gateway_crash.log")
  PREV=0
  [ -f "$MARKER.crash" ] && PREV=$(cat "$MARKER.crash")
  if [ "$LINES" -gt "$PREV" ]; then
    NEW=$(sed -n "$((PREV+1)),${LINES}p" "$LOG_DIR/tui_gateway_crash.log" | grep -c "thread exception")
    [ "$NEW" -gt 0 ] && PROBLEM="${PROBLEM}tui_gateway_crash.log: ${NEW} new thread exception(s)\n"
  fi
  echo "$LINES" > "$MARKER.crash"
fi

# --- 3. backend process alive? ---
if ! tasklist 2>/dev/null | grep -qiE "Hermes\.exe"; then
  PROBLEM="${PROBLEM}Hermes.exe process NOT running\n"
fi

# --- output only on problem ---
if [ -n "$PROBLEM" ]; then
  echo -e "⚠️ Gateway watchdog alert @ $(date '+%m-%d %H:%M'):\n${PROBLEM}Check: ~/AppData/Local/hermes/logs/desktop.log"
fi
