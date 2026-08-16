#!/data/data/com.termux/files/usr/bin/bash

# Lightweight service wrapper for Termux. Copy this file to ~/bin or run it
# from the checked-out repository. Configuration is kept in the repository.
set -u

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
BASE_DIR="${JOB_MONITOR_DIR:-$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)}"
CONFIG_FILE="${JOB_MONITOR_CONFIG:-$BASE_DIR/config.yaml}"
LOG_DIR="${JOB_MONITOR_LOG_DIR:-$BASE_DIR/logs}"
LOG_FILE="$LOG_DIR/job-monitor.log"
PID_FILE="$LOG_DIR/job-monitor.pid"
PYTHON_BIN="${JOB_MONITOR_PYTHON:-$BASE_DIR/.venv/bin/python}"

mkdir -p "$LOG_DIR"

is_running() {
    [ -f "$PID_FILE" ] && kill -0 "$(sed -n '1p' "$PID_FILE")" 2>/dev/null
}

start_worker() {
    if is_running; then
        echo "job-monitor is already running (pid $(sed -n '1p' "$PID_FILE"))"
        return 0
    fi
    rm -f "$PID_FILE"
    (
        echo "$BASHPID" > "$PID_FILE"
        trap 'if [ "${wake_lock:-0}" = 1 ]; then termux-wake-unlock; fi; rm -f "$PID_FILE"; exit 0' INT TERM EXIT
        wake_lock="${JOB_MONITOR_WAKE_LOCK:-0}"
        if [ "$wake_lock" = 1 ] && command -v termux-wake-lock >/dev/null 2>&1; then
            termux-wake-lock
        fi
        cd "$BASE_DIR" || exit 1
        while :; do
            JOB_MONITOR_LOG_FILE="$LOG_FILE" "$PYTHON_BIN" -m app.main --config "$CONFIG_FILE" run >/dev/null 2>&1
            status=$?
            echo "$(date -Iseconds) monitor exited status=$status; restarting in 30 seconds" >> "$LOG_FILE"
            sleep 30
        done
    ) >> "$LOG_FILE" 2>&1 &
    echo $! > "$PID_FILE"
    echo "job-monitor started (pid $(sed -n '1p' "$PID_FILE"))"
}

stop_worker() {
    if ! is_running; then
        rm -f "$PID_FILE"
        echo "job-monitor is not running"
        return 0
    fi
    pid="$(sed -n '1p' "$PID_FILE")"
    kill "$pid" 2>/dev/null || true
    for _ in 1 2 3 4 5; do
        is_running || break
        sleep 1
    done
    is_running && kill -9 "$pid" 2>/dev/null || true
    rm -f "$PID_FILE"
    echo "job-monitor stopped"
}

case "${1:-status}" in
    start) start_worker ;;
    stop) stop_worker ;;
    restart) stop_worker; start_worker ;;
    status)
        if is_running; then echo "job-monitor is running (pid $(sed -n '1p' "$PID_FILE"))"; else echo "job-monitor is stopped"; fi
        ;;
    logs) tail -n 100 -f "$LOG_FILE" ;;
    *) echo "Usage: $0 {start|stop|restart|status|logs}" >&2; exit 2 ;;
esac
