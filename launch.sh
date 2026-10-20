#!/usr/bin/env bash
# Dynamic Island launcher — waits for desktop session to be fully ready.

PYTHON="/home/noroot/Documents/Project-overhead/tmp/bin/python"
SCRIPT="/home/noroot/Documents/Project-overhead/main.py"
LOG="/home/noroot/.local/share/project-overhead/island.log"

mkdir -p "$(dirname "$LOG")"

# Wait up to 20s for a valid DISPLAY / WAYLAND session
for i in $(seq 1 20); do
    if [ -n "$DISPLAY" ] || [ -n "$WAYLAND_DISPLAY" ]; then
        break
    fi
    sleep 1
done

# Extra grace period so the WM/compositor is fully settled
sleep 3

exec "$PYTHON" "$SCRIPT" >> "$LOG" 2>&1
