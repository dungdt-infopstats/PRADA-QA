#!/bin/bash

# MASEE Test Runner
# Comprehensive test execution script

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

# Default settings
TEST_TYPE="all"
COVERAGE=false
VERBOSE=false
PARALLEL=false
REPORT_FORMAT="terminal"
OUTPUT_DIR="test_results"

show_usage() {
    echo "MASEE Test Runner"
    echo "================"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -t, --type TYPE         Test type: all, unit, integration, e2e, performance (default: all)"
    echo "  -c, --coverage          Generate coverage report"
    echo "  -v, --verbose           Verbose output"
    echo "  -p, --parallel          Run tests in parallel"
    echo "  -f, --format FORMAT     Report format: terminal, html, xml (default: terminal)"
    echo "  -o, --output-dir DIR    Output directory for reports (default: test_results)"
    echo "  --fast                  Run only fast tests (exclude slow markers)"
    echo "  --with-api              Include tests that require API keys"
    echo "  --no-network            Exclude tests that require network access"
    echo "  -h, --help              Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                                    # Run all tests"
    echo "  $0 -t unit -c                        # Run unit tests with coverage"
    echo "  $0 -t integration -v                 # Run integration tests verbosely"
    echo "  $0 -t performance --fast             # Run fast performance tests only"
    echo "  $0 --coverage -f html                # Generate HTML coverage report"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -t|--type)
            TEST_TYPE="$2"
            shift 2
            ;;
        -c|--coverage)
            COVERAGE=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -p|--parallel)
            PARALLEL=true
            shift
            ;;
        -f|--format)
            REPORT_FORMAT="$2"
            shift 2
            ;;
        -o|--output-dir)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        --fast)
            EXCLUDE_SLOW=true
            shift
            ;;
        --with-api)
            INCLUDE_API=true
            shift
            ;;
        --no-network)
            EXCLUDE_NETWORK=true
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

# Setup environment to use custom smolagents
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MASEE_SITE_PACKAGES="$PROJECT_ROOT/masee/Lib/site-packages"

if [ -d "$MASEE_SITE_PACKAGES/smolagents" ]; then
    export PYTHONPATH="${MASEE_SITE_PACKAGES}:${PROJECT_ROOT}/src:${PYTHONPATH}"
    print_info "Using custom smolagents from masee env"
else
    export PYTHONPATH="${PROJECT_ROOT}/src:${PYTHONPATH}"
    print_warning "Custom smolagents not found, using system installation"
fi

# Check if pytest is available
if ! command -v pytest &> /dev/null; then
    print_error "pytest not found! Please install it with: pip install pytest"
    exit 1
fi

# Create output directory
mkdir -p "$OUTPUT_DIR"

print_header "MASEE Test Runner"
print_info "Test type: $TEST_TYPE"
print_info "Coverage: $COVERAGE"
print_info "Output directory: $OUTPUT_DIR"
echo ""

# Build pytest command
PYTEST_ARGS="-v"

# Add coverage if requested
if [ "$COVERAGE" = true ]; then
    if command -v pytest-cov &> /dev/null; then
        PYTEST_ARGS="$PYTEST_ARGS --cov=src --cov-report=term-missing"

        if [ "$REPORT_FORMAT" = "html" ]; then
            PYTEST_ARGS="$PYTEST_ARGS --cov-report=html:$OUTPUT_DIR/coverage_html"
        elif [ "$REPORT_FORMAT" = "xml" ]; then
            PYTEST_ARGS="$PYTEST_ARGS --cov-report=xml:$OUTPUT_DIR/coverage.xml"
        fi
    else
        print_warning "pytest-cov not found. Install it with: pip install pytest-cov"
        print_info "Running tests without coverage..."
    fi
fi

# Add parallel execution if requested
if [ "$PARALLEL" = true ]; then
    if command -v pytest-xdist &> /dev/null; then
        PYTEST_ARGS="$PYTEST_ARGS -n auto"
    else
        print_warning "pytest-xdist not found. Install it with: pip install pytest-xdist"
        print_info "Running tests sequentially..."
    fi
fi

# Add verbose output if requested
if [ "$VERBOSE" = true ]; then
    PYTEST_ARGS="$PYTEST_ARGS -vv -s"
fi

# Add output format
if [ "$REPORT_FORMAT" = "xml" ]; then
    PYTEST_ARGS="$PYTEST_ARGS --junitxml=$OUTPUT_DIR/test_results.xml"
elif [ "$REPORT_FORMAT" = "html" ]; then
    if command -v pytest-html &> /dev/null; then
        PYTEST_ARGS="$PYTEST_ARGS --html=$OUTPUT_DIR/test_report.html --self-contained-html"
    else
        print_warning "pytest-html not found. Install it with: pip install pytest-html"
    fi
fi

# Set test paths and markers based on test type
case $TEST_TYPE in
    unit)
        TEST_PATHS="tests/unit"
        PYTEST_ARGS="$PYTEST_ARGS -m unit"
        ;;
    integration)
        TEST_PATHS="tests/integration"
        PYTEST_ARGS="$PYTEST_ARGS -m integration"
        ;;
    e2e)
        TEST_PATHS="tests/e2e"
        PYTEST_ARGS="$PYTEST_ARGS -m e2e"
        ;;
    performance)
        TEST_PATHS="tests/performance"
        PYTEST_ARGS="$PYTEST_ARGS -m performance"
        ;;
    all|*)
        TEST_PATHS="tests"
        ;;
esac

# Add marker exclusions
EXCLUSIONS=""

if [ "$EXCLUDE_SLOW" = true ]; then
    EXCLUSIONS="$EXCLUSIONS and not slow"
fi

if [ "$INCLUDE_API" != true ]; then
    EXCLUSIONS="$EXCLUSIONS and not requires_api"
fi

if [ "$EXCLUDE_NETWORK" = true ]; then
    EXCLUSIONS="$EXCLUSIONS and not requires_network"
fi

if [ -n "$EXCLUSIONS" ]; then
    # Remove leading " and " if present
    EXCLUSIONS=$(echo "$EXCLUSIONS" | sed 's/^ and //')
    PYTEST_ARGS="$PYTEST_ARGS -m 'not ($EXCLUSIONS)'"
fi

print_info "Running command: pytest $PYTEST_ARGS $TEST_PATHS"
echo ""

# Run the tests
START_TIME=$(date +%s)

if eval pytest $PYTEST_ARGS $TEST_PATHS; then
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))

    print_success "All tests passed! ✅"
    print_info "Test execution time: ${DURATION}s"

    # Show coverage summary if coverage was run
    if [ "$COVERAGE" = true ] && [ "$REPORT_FORMAT" = "html" ]; then
        print_info "Coverage report available at: $OUTPUT_DIR/coverage_html/index.html"
    fi

    # Show test report if HTML format was requested
    if [ "$REPORT_FORMAT" = "html" ] && [ -f "$OUTPUT_DIR/test_report.html" ]; then
        print_info "Test report available at: $OUTPUT_DIR/test_report.html"
    fi

else
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))

    print_error "Some tests failed! ❌"
    print_info "Test execution time: ${DURATION}s"

    # Still show reports for debugging
    if [ "$COVERAGE" = true ] && [ "$REPORT_FORMAT" = "html" ]; then
        print_info "Coverage report (partial) available at: $OUTPUT_DIR/coverage_html/index.html"
    fi

    if [ "$REPORT_FORMAT" = "html" ] && [ -f "$OUTPUT_DIR/test_report.html" ]; then
        print_info "Test report available at: $OUTPUT_DIR/test_report.html"
    fi

    exit 1
fi