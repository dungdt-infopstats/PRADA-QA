#!/bin/bash

# MASEE Experiment Monitor
# Monitor running experiments and show progress

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${CYAN}$1${NC}"
}

# Function to show running processes
show_running_processes() {
    print_header "Running Python Processes:"
    if pgrep -f "python.*main.py" > /dev/null; then
        ps aux | grep "python.*main.py" | grep -v grep | while read line; do
            echo "  $line"
        done
    else
        echo "  No MASEE experiments currently running"
    fi
    echo ""
}

# Function to show recent log files
show_recent_logs() {
    print_header "Recent Log Files:"
    if ls *_log_*.txt &> /dev/null; then
        ls -lt *_log_*.txt | head -10 | while read line; do
            echo "  $line"
        done
    else
        echo "  No log files found in current directory"
    fi
    echo ""
}

# Function to monitor log file in real-time
monitor_log() {
    local log_file="$1"

    if [ ! -f "$log_file" ]; then
        print_error "Log file not found: $log_file"
        return 1
    fi

    print_info "Monitoring log file: $log_file"
    print_info "Press Ctrl+C to stop monitoring"
    echo ""

    tail -f "$log_file" | while read line; do
        # Color code different types of messages
        if echo "$line" | grep -i "error\|failed\|exception" > /dev/null; then
            echo -e "${RED}$line${NC}"
        elif echo "$line" | grep -i "success\|completed\|finished" > /dev/null; then
            echo -e "${GREEN}$line${NC}"
        elif echo "$line" | grep -i "warning" > /dev/null; then
            echo -e "${YELLOW}$line${NC}"
        elif echo "$line" | grep -i "info\|processing\|running" > /dev/null; then
            echo -e "${BLUE}$line${NC}"
        else
            echo "$line"
        fi
    done
}

# Function to show experiment statistics
show_statistics() {
    print_header "Experiment Statistics:"

    local total_logs=$(ls *_log_*.txt 2>/dev/null | wc -l)
    local running_procs=$(pgrep -f "python.*main.py" | wc -l)

    echo "  Total log files: $total_logs"
    echo "  Running experiments: $running_procs"

    if [ $total_logs -gt 0 ]; then
        local completed=$(grep -l "Saved results\|evaluation completed" *_log_*.txt 2>/dev/null | wc -l)
        local failed=$(grep -l "Error\|Failed\|Exception" *_log_*.txt 2>/dev/null | wc -l)

        echo "  Completed experiments: $completed"
        echo "  Failed experiments: $failed"
        echo "  Success rate: $(( completed * 100 / total_logs ))%"
    fi
    echo ""
}

# Function to kill all running experiments
kill_experiments() {
    print_warning "Killing all running MASEE experiments..."

    if pgrep -f "python.*main.py" > /dev/null; then
        pkill -f "python.*main.py"
        print_success "All experiments terminated"
    else
        print_info "No running experiments found"
    fi
}

# Function to show help
show_help() {
    echo "MASEE Experiment Monitor"
    echo "======================="
    echo ""
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  status                Show running processes and recent logs"
    echo "  monitor <logfile>     Monitor a specific log file in real-time"
    echo "  stats                 Show experiment statistics"
    echo "  kill                  Kill all running experiments"
    echo "  clean                 Clean up old log files"
    echo "  help                  Show this help message"
    echo ""
    echo "Options:"
    echo "  -w, --watch SECONDS   Refresh interval for status (default: 5)"
    echo "  -n, --lines N         Number of recent logs to show (default: 10)"
}

# Function to clean up old log files
clean_logs() {
    print_info "Cleaning up log files..."

    # Ask for confirmation
    read -p "Delete log files older than 7 days? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        find . -name "*_log_*.txt" -mtime +7 -delete
        print_success "Old log files cleaned up"
    else
        print_info "Cleanup cancelled"
    fi
}

# Main function
main() {
    local command="${1:-status}"
    local watch_interval=5
    local num_lines=10

    # Parse options
    while [[ $# -gt 1 ]]; do
        case $2 in
            -w|--watch)
                watch_interval="$3"
                shift 2
                ;;
            -n|--lines)
                num_lines="$3"
                shift 2
                ;;
            *)
                shift
                ;;
        esac
    done

    case $command in
        status)
            if [ "$2" = "--watch" ] || [ "$3" = "--watch" ]; then
                print_info "Watching experiment status (refresh every ${watch_interval}s)"
                print_info "Press Ctrl+C to stop"
                while true; do
                    clear
                    echo "MASEE Experiment Monitor - $(date)"
                    echo "=================================="
                    echo ""
                    show_running_processes
                    show_recent_logs
                    show_statistics
                    sleep "$watch_interval"
                done
            else
                show_running_processes
                show_recent_logs
                show_statistics
            fi
            ;;
        monitor)
            if [ -z "$2" ]; then
                print_error "Please specify a log file to monitor"
                echo "Usage: $0 monitor <logfile>"
                exit 1
            fi
            monitor_log "$2"
            ;;
        stats)
            show_statistics
            ;;
        kill)
            kill_experiments
            ;;
        clean)
            clean_logs
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            print_error "Unknown command: $command"
            show_help
            exit 1
            ;;
    esac
}

# Check if running with no arguments
if [ $# -eq 0 ]; then
    main status
else
    main "$@"
fi