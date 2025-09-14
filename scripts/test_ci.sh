#!/bin/bash

# MASEE CI Test Runner
# Optimized for continuous integration environments

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

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# CI environment detection
CI_ENV=""
if [ -n "$GITHUB_ACTIONS" ]; then
    CI_ENV="github"
elif [ -n "$GITLAB_CI" ]; then
    CI_ENV="gitlab"
elif [ -n "$JENKINS_URL" ]; then
    CI_ENV="jenkins"
elif [ -n "$CI" ]; then
    CI_ENV="generic"
fi

print_info "Running in CI environment: ${CI_ENV:-local}"

# Install test dependencies if not already installed
print_info "Installing test dependencies..."
pip install -q pytest pytest-cov pytest-xdist pytest-html pytest-timeout

# Create results directory
mkdir -p test_results

# Setup environment to use custom smolagents
PROJECT_ROOT="$(pwd)"
MASEE_SITE_PACKAGES="$PROJECT_ROOT/masee/Lib/site-packages"

if [ -d "$MASEE_SITE_PACKAGES/smolagents" ]; then
    export PYTHONPATH="${MASEE_SITE_PACKAGES}:${PROJECT_ROOT}/src:${PYTHONPATH}"
    print_info "Using custom smolagents from masee env"
else
    export PYTHONPATH="${PROJECT_ROOT}/src:${PYTHONPATH}"
    print_warning "Custom smolagents not found, using system installation"
fi

export PYTHONUNBUFFERED=1

# Define test stages
run_unit_tests() {
    print_info "Running unit tests..."
    pytest tests/unit \
        --cov=src \
        --cov-report=term-missing \
        --cov-report=xml:test_results/coverage.xml \
        --cov-report=html:test_results/coverage_html \
        --junitxml=test_results/unit_tests.xml \
        --tb=short \
        -v \
        -m "not slow and not requires_api and not requires_network"
}

run_integration_tests() {
    print_info "Running integration tests..."
    pytest tests/integration \
        --junitxml=test_results/integration_tests.xml \
        --tb=short \
        -v \
        -m "not slow and not requires_api and not requires_network"
}

run_e2e_tests() {
    print_info "Running end-to-end tests..."
    pytest tests/e2e \
        --junitxml=test_results/e2e_tests.xml \
        --tb=short \
        -v \
        --timeout=300 \
        -m "not slow and not requires_network"
}

run_performance_tests() {
    print_info "Running performance tests..."
    pytest tests/performance \
        --junitxml=test_results/performance_tests.xml \
        --tb=short \
        -v \
        -m "not slow and not requires_api and not requires_network"
}

run_code_quality_checks() {
    print_info "Running code quality checks..."

    # Install quality tools if available
    if command -v flake8 &> /dev/null; then
        print_info "Running flake8..."
        flake8 src --max-line-length=100 --ignore=E203,W503 --output-file=test_results/flake8.txt || true
    fi

    if command -v black &> /dev/null; then
        print_info "Checking code formatting with black..."
        black --check --diff src tests || {
            print_warning "Code formatting issues found. Run 'black src tests' to fix."
        }
    fi

    if command -v mypy &> /dev/null; then
        print_info "Running type checks with mypy..."
        mypy src --ignore-missing-imports --output-file=test_results/mypy.txt || true
    fi
}

generate_summary_report() {
    print_info "Generating test summary report..."

    cat > test_results/summary.md << 'EOF'
# MASEE Test Results Summary

## Test Execution Results

EOF

    # Add unit test results
    if [ -f "test_results/unit_tests.xml" ]; then
        UNIT_TESTS=$(grep -o 'tests="[0-9]*"' test_results/unit_tests.xml | cut -d'"' -f2)
        UNIT_FAILURES=$(grep -o 'failures="[0-9]*"' test_results/unit_tests.xml | cut -d'"' -f2)
        UNIT_ERRORS=$(grep -o 'errors="[0-9]*"' test_results/unit_tests.xml | cut -d'"' -f2)

        echo "### Unit Tests" >> test_results/summary.md
        echo "- Total: $UNIT_TESTS" >> test_results/summary.md
        echo "- Failures: $UNIT_FAILURES" >> test_results/summary.md
        echo "- Errors: $UNIT_ERRORS" >> test_results/summary.md
        echo "" >> test_results/summary.md
    fi

    # Add integration test results
    if [ -f "test_results/integration_tests.xml" ]; then
        INT_TESTS=$(grep -o 'tests="[0-9]*"' test_results/integration_tests.xml | cut -d'"' -f2)
        INT_FAILURES=$(grep -o 'failures="[0-9]*"' test_results/integration_tests.xml | cut -d'"' -f2)
        INT_ERRORS=$(grep -o 'errors="[0-9]*"' test_results/integration_tests.xml | cut -d'"' -f2)

        echo "### Integration Tests" >> test_results/summary.md
        echo "- Total: $INT_TESTS" >> test_results/summary.md
        echo "- Failures: $INT_FAILURES" >> test_results/summary.md
        echo "- Errors: $INT_ERRORS" >> test_results/summary.md
        echo "" >> test_results/summary.md
    fi

    # Add coverage information if available
    if [ -f "test_results/coverage.xml" ]; then
        COVERAGE=$(grep -o 'line-rate="[0-9.]*"' test_results/coverage.xml | head -1 | cut -d'"' -f2)
        COVERAGE_PERCENT=$(echo "$COVERAGE * 100" | bc -l | cut -d. -f1)

        echo "### Code Coverage" >> test_results/summary.md
        echo "- Coverage: ${COVERAGE_PERCENT}%" >> test_results/summary.md
        echo "" >> test_results/summary.md
    fi

    echo "## Artifacts" >> test_results/summary.md
    echo "- Coverage Report: test_results/coverage_html/index.html" >> test_results/summary.md
    echo "- Test Results: test_results/*.xml" >> test_results/summary.md
}

# Main execution
print_info "Starting MASEE CI test pipeline..."
START_TIME=$(date +%s)

FAILED_STAGES=()

# Run test stages
if ! run_unit_tests; then
    FAILED_STAGES+=("unit_tests")
    print_error "Unit tests failed!"
fi

if ! run_integration_tests; then
    FAILED_STAGES+=("integration_tests")
    print_error "Integration tests failed!"
fi

if ! run_e2e_tests; then
    FAILED_STAGES+=("e2e_tests")
    print_error "E2E tests failed!"
fi

if ! run_performance_tests; then
    FAILED_STAGES+=("performance_tests")
    print_error "Performance tests failed!"
fi

# Run code quality checks (non-blocking)
run_code_quality_checks

# Generate summary report
generate_summary_report

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

# Print results
echo ""
print_info "CI Pipeline completed in ${DURATION}s"

if [ ${#FAILED_STAGES[@]} -eq 0 ]; then
    print_success "All test stages passed! ✅"

    # Set GitHub Actions output if running in GitHub
    if [ "$CI_ENV" = "github" ]; then
        echo "test_result=success" >> $GITHUB_OUTPUT
    fi

    exit 0
else
    print_error "Failed stages: ${FAILED_STAGES[*]}"

    # Set GitHub Actions output if running in GitHub
    if [ "$CI_ENV" = "github" ]; then
        echo "test_result=failure" >> $GITHUB_OUTPUT
        echo "failed_stages=${FAILED_STAGES[*]}" >> $GITHUB_OUTPUT
    fi

    exit 1
fi