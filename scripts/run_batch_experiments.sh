#!/bin/bash

# MASEE Batch Experiment Runner
# Run multiple experiments in sequence or parallel

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Configuration arrays - modify these for your experiments
MODELS=(
    "gpt-4o-mini"
    "qwen2.5-coder:32b"
    "llama3.3:70b-instruct-q8_0"
)

EXPERIMENTS=(
    "qafirst-qav-attv-description-summerize"
    "qafirst-qav-attv-webtv-description-summerize"
    "base-description"
)

PARTS=("100")
DATA_CHOICES=("car" "acs")
STEPS=("3" "5" "9")

# Default settings
PARALLEL=false
MAX_PARALLEL=3
DRY_RUN=false

show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -p, --parallel              Run experiments in parallel"
    echo "  -j, --jobs N                Maximum parallel jobs (default: $MAX_PARALLEL)"
    echo "  --dry-run                   Show what would be run without executing"
    echo "  -h, --help                  Show this help message"
    echo ""
    echo "Configuration:"
    echo "  Models: ${MODELS[*]}"
    echo "  Experiments: ${EXPERIMENTS[*]}"
    echo "  Parts: ${PARTS[*]}"
    echo "  Data Choices: ${DATA_CHOICES[*]}"
    echo "  Steps: ${STEPS[*]}"
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -p|--parallel)
            PARALLEL=true
            shift
            ;;
        -j|--jobs)
            MAX_PARALLEL="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=true
            shift
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

# Function to run single experiment
run_single_experiment() {
    local model="$1"
    local experiment="$2"
    local part="$3"
    local data_choice="$4"
    local step="$5"

    local timestamp=$(date '+%Y-%m-%d_%H-%M-%S')
    local model_clean=$(echo "$model" | sed 's/[.:\/]/_/g')
    local log_file="${data_choice}_log_${model_clean}_${experiment}_${part}_${step}_${timestamp}.txt"

    if [ "$DRY_RUN" = true ]; then
        echo "Would run: python src/main.py '$model' '$experiment' '$part' '$data_choice' '$step' > '$log_file' 2>&1"
        return 0
    fi

    print_info "Starting: $model | $experiment | Part $part | $data_choice | $step steps"

    if python src/main.py "$model" "$experiment" "$part" "$data_choice" "$step" > "$log_file" 2>&1; then
        print_success "Completed: $model | $experiment | Part $part | $data_choice | $step steps"
        echo "  Log: $log_file"
        return 0
    else
        print_error "Failed: $model | $experiment | Part $part | $data_choice | $step steps"
        echo "  Log: $log_file"
        return 1
    fi
}

# Calculate total number of experiments
total_experiments=0
for model in "${MODELS[@]}"; do
    for experiment in "${EXPERIMENTS[@]}"; do
        for part in "${PARTS[@]}"; do
            for data_choice in "${DATA_CHOICES[@]}"; do
                for step in "${STEPS[@]}"; do
                    ((total_experiments++))
                done
            done
        done
    done
done

print_info "Total experiments to run: $total_experiments"

if [ "$DRY_RUN" = true ]; then
    print_info "DRY RUN MODE - No experiments will actually be executed"
fi

if [ "$PARALLEL" = true ]; then
    print_info "Running experiments in parallel (max $MAX_PARALLEL jobs)"
else
    print_info "Running experiments sequentially"
fi

echo ""

# Run experiments
experiment_count=0
failed_count=0

if [ "$PARALLEL" = true ]; then
    # Parallel execution with job control
    job_count=0

    for model in "${MODELS[@]}"; do
        for experiment in "${EXPERIMENTS[@]}"; do
            for part in "${PARTS[@]}"; do
                for data_choice in "${DATA_CHOICES[@]}"; do
                    for step in "${STEPS[@]}"; do
                        ((experiment_count++))

                        # Wait for available slot if at max jobs
                        while [ $(jobs -r | wc -l) -ge "$MAX_PARALLEL" ]; do
                            sleep 1
                        done

                        # Run experiment in background
                        (
                            if ! run_single_experiment "$model" "$experiment" "$part" "$data_choice" "$step"; then
                                exit 1
                            fi
                        ) &

                        ((job_count++))
                    done
                done
            done
        done
    done

    # Wait for all background jobs to complete
    print_info "Waiting for all experiments to complete..."
    wait

    # Count failures (this is approximate with parallel execution)
    failed_count=0
    for job in $(jobs -l | grep -c "Exit" || true); do
        ((failed_count++))
    done

else
    # Sequential execution
    for model in "${MODELS[@]}"; do
        for experiment in "${EXPERIMENTS[@]}"; do
            for part in "${PARTS[@]}"; do
                for data_choice in "${DATA_CHOICES[@]}"; do
                    for step in "${STEPS[@]}"; do
                        ((experiment_count++))

                        if ! run_single_experiment "$model" "$experiment" "$part" "$data_choice" "$step"; then
                            ((failed_count++))
                        fi

                        echo ""
                    done
                done
            done
        done
    done
fi

# Final summary
echo ""
print_info "Batch experiment summary:"
echo "  Total experiments: $total_experiments"
echo "  Completed: $((experiment_count - failed_count))"
echo "  Failed: $failed_count"

if [ $failed_count -eq 0 ]; then
    print_success "All experiments completed successfully!"
else
    print_error "$failed_count experiments failed. Check the log files for details."
    exit 1
fi