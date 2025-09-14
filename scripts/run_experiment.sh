#!/bin/bash

# MASEE Experiment Runner
# Enhanced bash script for running multi-agent system experiments

set -e  # Exit on any error

# Default configuration
DEFAULT_MODEL="gpt-4o-mini"
DEFAULT_EXPERIMENT="qafirst-qav-attv-description-summerize"
DEFAULT_PART="100"
DEFAULT_DATA_CHOICE="car"
DEFAULT_STEP="3"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
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

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -m, --model MODEL_NAME          Model to use (default: $DEFAULT_MODEL)"
    echo "  -e, --experiment EXPERIMENT     Experiment type (default: $DEFAULT_EXPERIMENT)"
    echo "  -p, --part PART                 Part number (default: $DEFAULT_PART)"
    echo "  -d, --data DATA_CHOICE          Data choice (default: $DEFAULT_DATA_CHOICE)"
    echo "  -s, --steps STEPS               Number of steps (default: $DEFAULT_STEP)"
    echo "  -l, --log-dir LOG_DIR           Log directory (default: logs)"
    echo "  -h, --help                      Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 --model gpt-4o-mini --experiment base --part 50 --data car --steps 5"
    echo "  $0 -m qwen2.5-coder:32b -e qafirst-qav-attv-webtv-description-summerize -p 100 -d acs -s 9"
}

# Parse command line arguments
MODEL="$DEFAULT_MODEL"
EXPERIMENT="$DEFAULT_EXPERIMENT"
PART="$DEFAULT_PART"
DATA_CHOICE="$DEFAULT_DATA_CHOICE"
STEP="$DEFAULT_STEP"
LOG_DIR="logs"

while [[ $# -gt 0 ]]; do
    case $1 in
        -m|--model)
            MODEL="$2"
            shift 2
            ;;
        -e|--experiment)
            EXPERIMENT="$2"
            shift 2
            ;;
        -p|--part)
            PART="$2"
            shift 2
            ;;
        -d|--data)
            DATA_CHOICE="$2"
            shift 2
            ;;
        -s|--steps)
            STEP="$2"
            shift 2
            ;;
        -l|--log-dir)
            LOG_DIR="$2"
            shift 2
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Create timestamp for logging
TIMESTAMP=$(date '+%Y-%m-%d_%H-%M-%S')
MODEL_CLEAN=$(echo "$MODEL" | sed 's/[.:\/]/_/g')
LOG_FILE="${DATA_CHOICE}_log_${MODEL_CLEAN}_${EXPERIMENT}_${PART}_${TIMESTAMP}.txt"

# Print configuration
print_info "Starting MASEE experiment with the following configuration:"
echo "  Model: $MODEL"
echo "  Experiment: $EXPERIMENT"
echo "  Part: $PART"
echo "  Data Choice: $DATA_CHOICE"
echo "  Steps: $STEP"
echo "  Log File: $LOG_FILE"
echo ""

# Check if required files exist
print_info "Checking prerequisites..."

if [ ! -f "src/main.py" ]; then
    print_error "src/main.py not found! Make sure you're in the project root directory."
    exit 1
fi

if [ ! -f "data/${DATA_CHOICE}_pqa_validation_part${PART}.csv" ]; then
    print_warning "Data file data/${DATA_CHOICE}_pqa_validation_part${PART}.csv not found!"
    print_info "Continuing anyway - the script will create it if needed."
fi

# Create log directory if it doesn't exist
mkdir -p "$LOG_DIR"

print_success "Prerequisites check completed."

# Run the experiment
print_info "Running experiment: python src/main.py \"$MODEL\" \"$EXPERIMENT\" \"$PART\" \"$DATA_CHOICE\" \"$STEP\""

# Execute the Python script and capture output
if python src/main.py "$MODEL" "$EXPERIMENT" "$PART" "$DATA_CHOICE" "$STEP" 2>&1 | tee "$LOG_FILE"; then
    print_success "Experiment completed successfully!"
    print_info "Results saved to: $LOG_FILE"
else
    print_error "Experiment failed! Check the log file: $LOG_FILE"
    exit 1
fi

# Show final summary
echo ""
print_success "Experiment Summary:"
echo "  Configuration: $MODEL | $EXPERIMENT | Part $PART | $DATA_CHOICE | $STEP steps"
echo "  Log file: $LOG_FILE"
echo "  Status: Completed"