#!/bin/bash

# MASEE Test Environment Setup
# Sets up environment to use custom smolagents from masee env

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Get the project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MASEE_SITE_PACKAGES="$PROJECT_ROOT/masee/Lib/site-packages"

print_info "Setting up MASEE test environment..."
print_info "Project root: $PROJECT_ROOT"
print_info "Custom smolagents path: $MASEE_SITE_PACKAGES"

# Check if masee env smolagents exists
if [ -d "$MASEE_SITE_PACKAGES/smolagents" ]; then
    print_success "Found custom smolagents in masee env"
else
    print_info "Custom smolagents not found, will use system installation if available"
fi

# Set up environment variables
export PYTHONPATH="${MASEE_SITE_PACKAGES}:${PROJECT_ROOT}/src:${PYTHONPATH}"
export MASEE_USE_CUSTOM_SMOLAGENTS=1
export MASEE_PROJECT_ROOT="$PROJECT_ROOT"

print_info "Environment variables set:"
echo "  PYTHONPATH: $PYTHONPATH"
echo "  MASEE_USE_CUSTOM_SMOLAGENTS: $MASEE_USE_CUSTOM_SMOLAGENTS"
echo "  MASEE_PROJECT_ROOT: $MASEE_PROJECT_ROOT"

print_success "Test environment setup complete!"

# If called with arguments, execute them with the environment
if [ $# -gt 0 ]; then
    print_info "Executing: $@"
    exec "$@"
fi