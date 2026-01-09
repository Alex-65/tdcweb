#!/bin/bash
#
# TDC Development Server Manager
# Usage: ./dev.sh [command] [service] [options]
#
# Commands: start, stop, restart, status, logs
# Services: all, backend, frontend (default: all)
# Options:  -a, --attached  Run in foreground (default: detached)
#

set -e

# ============================================
# Configuration
# ============================================
PROJECT_ROOT="/data1/tdcweb-dev"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
PID_DIR="$PROJECT_ROOT/.pids"
LOG_DIR="$PROJECT_ROOT/.logs"

BACKEND_PORT=9502
FRONTEND_PORT=9503

BACKEND_PID_FILE="$PID_DIR/backend.pid"
FRONTEND_PID_FILE="$PID_DIR/frontend.pid"
BACKEND_LOG="$LOG_DIR/backend.log"
FRONTEND_LOG="$LOG_DIR/frontend.log"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ============================================
# Helper Functions
# ============================================
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

ensure_dirs() {
    mkdir -p "$PID_DIR" "$LOG_DIR"
}

is_running() {
    local pid_file="$1"
    if [[ -f "$pid_file" ]]; then
        local pid=$(cat "$pid_file")
        if ps -p "$pid" > /dev/null 2>&1; then
            return 0
        fi
    fi
    return 1
}

get_pid() {
    local pid_file="$1"
    if [[ -f "$pid_file" ]]; then
        cat "$pid_file"
    fi
}

wait_for_port() {
    local port="$1"
    local timeout="${2:-30}"
    local count=0

    while ! nc -z localhost "$port" 2>/dev/null; do
        sleep 1
        count=$((count + 1))
        if [[ $count -ge $timeout ]]; then
            return 1
        fi
    done
    return 0
}

# ============================================
# Backend Functions
# ============================================
start_backend() {
    local attached="$1"

    if is_running "$BACKEND_PID_FILE"; then
        log_warn "Backend already running (PID: $(get_pid "$BACKEND_PID_FILE"))"
        return 0
    fi

    log_info "Starting backend on port $BACKEND_PORT..."

    cd "$BACKEND_DIR"

    # Activate venv if exists
    if [[ -f "venv/bin/activate" ]]; then
        source venv/bin/activate
    fi

    if [[ "$attached" == "true" ]]; then
        # Attached mode - run in foreground
        log_info "Running in attached mode (Ctrl+C to stop)"
        FLASK_APP=wsgi.py FLASK_ENV=development flask run --host=0.0.0.0 --port=$BACKEND_PORT
    else
        # Detached mode - run in background
        FLASK_APP=wsgi.py FLASK_ENV=development flask run --host=0.0.0.0 --port=$BACKEND_PORT > "$BACKEND_LOG" 2>&1 &
        local pid=$!
        echo "$pid" > "$BACKEND_PID_FILE"

        # Wait for startup
        if wait_for_port $BACKEND_PORT 10; then
            log_success "Backend started (PID: $pid) - http://localhost:$BACKEND_PORT"
        else
            log_error "Backend failed to start. Check logs: $BACKEND_LOG"
            rm -f "$BACKEND_PID_FILE"
            return 1
        fi
    fi
}

stop_backend() {
    if ! is_running "$BACKEND_PID_FILE"; then
        log_warn "Backend not running"
        rm -f "$BACKEND_PID_FILE"
        return 0
    fi

    local pid=$(get_pid "$BACKEND_PID_FILE")
    log_info "Stopping backend (PID: $pid)..."

    kill "$pid" 2>/dev/null || true

    # Wait for process to stop
    local count=0
    while ps -p "$pid" > /dev/null 2>&1; do
        sleep 1
        count=$((count + 1))
        if [[ $count -ge 10 ]]; then
            log_warn "Force killing backend..."
            kill -9 "$pid" 2>/dev/null || true
            break
        fi
    done

    rm -f "$BACKEND_PID_FILE"
    log_success "Backend stopped"
}

status_backend() {
    if is_running "$BACKEND_PID_FILE"; then
        local pid=$(get_pid "$BACKEND_PID_FILE")
        echo -e "Backend:  ${GREEN}RUNNING${NC} (PID: $pid) - http://localhost:$BACKEND_PORT"
    else
        echo -e "Backend:  ${RED}STOPPED${NC}"
        rm -f "$BACKEND_PID_FILE"
    fi
}

# ============================================
# Frontend Functions
# ============================================
start_frontend() {
    local attached="$1"

    if is_running "$FRONTEND_PID_FILE"; then
        log_warn "Frontend already running (PID: $(get_pid "$FRONTEND_PID_FILE"))"
        return 0
    fi

    log_info "Starting frontend on port $FRONTEND_PORT..."

    cd "$FRONTEND_DIR"

    # Check if node_modules exists
    if [[ ! -d "node_modules" ]]; then
        log_info "Installing npm dependencies..."
        npm install
    fi

    if [[ "$attached" == "true" ]]; then
        # Attached mode - run in foreground
        log_info "Running in attached mode (Ctrl+C to stop)"
        npm run dev -- --host 0.0.0.0 --port $FRONTEND_PORT
    else
        # Detached mode - run in background
        npm run dev -- --host 0.0.0.0 --port $FRONTEND_PORT > "$FRONTEND_LOG" 2>&1 &
        local pid=$!
        echo "$pid" > "$FRONTEND_PID_FILE"

        # Wait for startup
        if wait_for_port $FRONTEND_PORT 30; then
            log_success "Frontend started (PID: $pid) - http://localhost:$FRONTEND_PORT"
        else
            log_error "Frontend failed to start. Check logs: $FRONTEND_LOG"
            rm -f "$FRONTEND_PID_FILE"
            return 1
        fi
    fi
}

stop_frontend() {
    if ! is_running "$FRONTEND_PID_FILE"; then
        log_warn "Frontend not running"
        rm -f "$FRONTEND_PID_FILE"
        return 0
    fi

    local pid=$(get_pid "$FRONTEND_PID_FILE")
    log_info "Stopping frontend (PID: $pid)..."

    # Kill process group (npm spawns child processes)
    pkill -P "$pid" 2>/dev/null || true
    kill "$pid" 2>/dev/null || true

    # Wait for process to stop
    local count=0
    while ps -p "$pid" > /dev/null 2>&1; do
        sleep 1
        count=$((count + 1))
        if [[ $count -ge 10 ]]; then
            log_warn "Force killing frontend..."
            pkill -9 -P "$pid" 2>/dev/null || true
            kill -9 "$pid" 2>/dev/null || true
            break
        fi
    done

    rm -f "$FRONTEND_PID_FILE"
    log_success "Frontend stopped"
}

status_frontend() {
    if is_running "$FRONTEND_PID_FILE"; then
        local pid=$(get_pid "$FRONTEND_PID_FILE")
        echo -e "Frontend: ${GREEN}RUNNING${NC} (PID: $pid) - http://localhost:$FRONTEND_PORT"
    else
        echo -e "Frontend: ${RED}STOPPED${NC}"
        rm -f "$FRONTEND_PID_FILE"
    fi
}

# ============================================
# Combined Functions
# ============================================
start_all() {
    local attached="$1"

    if [[ "$attached" == "true" ]]; then
        log_error "Cannot run both services in attached mode. Use: ./dev.sh start backend -a"
        exit 1
    fi

    start_backend "false"
    start_frontend "false"
}

stop_all() {
    stop_frontend
    stop_backend
}

restart_all() {
    local attached="$1"
    stop_all
    sleep 2
    start_all "$attached"
}

status_all() {
    echo ""
    echo "=== TDC Development Servers ==="
    echo ""
    status_backend
    status_frontend
    echo ""
}

show_logs() {
    local service="$1"

    case "$service" in
        backend)
            if [[ -f "$BACKEND_LOG" ]]; then
                tail -f "$BACKEND_LOG"
            else
                log_error "Backend log not found: $BACKEND_LOG"
            fi
            ;;
        frontend)
            if [[ -f "$FRONTEND_LOG" ]]; then
                tail -f "$FRONTEND_LOG"
            else
                log_error "Frontend log not found: $FRONTEND_LOG"
            fi
            ;;
        all)
            log_info "Showing logs for both services (Ctrl+C to stop)"
            tail -f "$BACKEND_LOG" "$FRONTEND_LOG" 2>/dev/null
            ;;
        *)
            log_error "Unknown service: $service"
            exit 1
            ;;
    esac
}

# ============================================
# Usage
# ============================================
show_usage() {
    cat << EOF
TDC Development Server Manager

Usage: ./dev.sh [command] [service] [options]

Commands:
  start     Start development server(s)
  stop      Stop development server(s)
  restart   Restart development server(s)
  status    Show server status
  logs      Follow server logs

Services:
  all       Both backend and frontend (default)
  backend   Flask backend only (port $BACKEND_PORT)
  frontend  Vue frontend only (port $FRONTEND_PORT)

Options:
  -a, --attached    Run in foreground (attached mode)
                    Only works with single service

Examples:
  ./dev.sh start              # Start all services (detached)
  ./dev.sh start backend      # Start backend only (detached)
  ./dev.sh start backend -a   # Start backend in foreground
  ./dev.sh stop               # Stop all services
  ./dev.sh restart frontend   # Restart frontend
  ./dev.sh status             # Show status of all services
  ./dev.sh logs backend       # Follow backend logs

Log files:
  Backend:  $BACKEND_LOG
  Frontend: $FRONTEND_LOG

EOF
}

# ============================================
# Main
# ============================================
main() {
    ensure_dirs

    local command="${1:-}"
    local service="${2:-all}"
    local attached="false"

    # Parse options
    for arg in "$@"; do
        case "$arg" in
            -a|--attached)
                attached="true"
                ;;
        esac
    done

    # Handle service as third argument if -a is second
    if [[ "$service" == "-a" || "$service" == "--attached" ]]; then
        service="all"
    fi

    case "$command" in
        start)
            case "$service" in
                all)
                    start_all "$attached"
                    ;;
                backend)
                    start_backend "$attached"
                    ;;
                frontend)
                    start_frontend "$attached"
                    ;;
                *)
                    log_error "Unknown service: $service"
                    show_usage
                    exit 1
                    ;;
            esac
            ;;
        stop)
            case "$service" in
                all)
                    stop_all
                    ;;
                backend)
                    stop_backend
                    ;;
                frontend)
                    stop_frontend
                    ;;
                *)
                    log_error "Unknown service: $service"
                    exit 1
                    ;;
            esac
            ;;
        restart)
            case "$service" in
                all)
                    restart_all "$attached"
                    ;;
                backend)
                    stop_backend
                    sleep 1
                    start_backend "$attached"
                    ;;
                frontend)
                    stop_frontend
                    sleep 1
                    start_frontend "$attached"
                    ;;
                *)
                    log_error "Unknown service: $service"
                    exit 1
                    ;;
            esac
            ;;
        status)
            status_all
            ;;
        logs)
            show_logs "$service"
            ;;
        -h|--help|help)
            show_usage
            ;;
        "")
            show_usage
            ;;
        *)
            log_error "Unknown command: $command"
            show_usage
            exit 1
            ;;
    esac
}

main "$@"
