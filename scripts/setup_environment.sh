#!/bin/bash

# MASEE Environment Setup Script
# Sets up the Python environment and dependencies

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

# Check if Python is available
check_python() {
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
    else
        print_error "Python not found! Please install Python 3.7 or later."
        exit 1
    fi

    # Check Python version
    PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | cut -d' ' -f2)
    print_info "Found Python $PYTHON_VERSION"

    # Check if version is >= 3.7
    if ! $PYTHON_CMD -c "import sys; exit(0 if sys.version_info >= (3, 7) else 1)"; then
        print_error "Python 3.7 or later is required. Found: $PYTHON_VERSION"
        exit 1
    fi
}

# Create virtual environment
create_venv() {
    print_info "Creating virtual environment..."

    if [ -d "masee_env" ]; then
        print_warning "Virtual environment already exists. Removing it..."
        rm -rf masee_env
    fi

    $PYTHON_CMD -m venv masee_env

    # Activate virtual environment
    source masee_env/bin/activate || source masee_env/Scripts/activate

    print_success "Virtual environment created and activated"
}

# Install dependencies
install_dependencies() {
    print_info "Installing Python dependencies..."

    # Upgrade pip first
    pip install --upgrade pip

    # Install core dependencies
    pip install \
        pandas \
        pyyaml \
        python-dotenv \
        jsonlines \
        langchain \
        langchain-community \
        langchain-openai \
        smolagents \
        selenium \
        helium \
        pillow \
        faiss-cpu \
        openai \
        tavily-python

    print_success "Dependencies installed"
}

# Create directory structure
create_directories() {
    print_info "Creating directory structure..."

    directories=(
        "data"
        "logs"
        "config/experiment"
        "config/evaluation"
        "results"
    )

    for dir in "${directories[@]}"; do
        mkdir -p "$dir"
        print_info "Created directory: $dir"
    done

    print_success "Directory structure created"
}

# Check for required files
check_files() {
    print_info "Checking for required configuration files..."

    required_files=(
        "path_config.yaml"
        "config/experiment.yaml"
        "config/meta_agent.yaml"
    )

    missing_files=()

    for file in "${required_files[@]}"; do
        if [ ! -f "$file" ]; then
            missing_files+=("$file")
        fi
    done

    if [ ${#missing_files[@]} -gt 0 ]; then
        print_warning "Missing configuration files:"
        for file in "${missing_files[@]}"; do
            echo "  - $file"
        done
        print_info "Please create these files before running experiments."
    else
        print_success "All required configuration files found"
    fi
}

# Create sample .env file
create_env_file() {
    if [ ! -f ".env" ]; then
        print_info "Creating sample .env file..."
        cat > .env << 'EOF'
# OpenAI API Key
OPENAI_API_KEY=your_openai_api_key_here

# Tavily API Key (for web search)
TAVILY_API_KEY=your_tavily_api_key_here

# Other API keys as needed
# ANTHROPIC_API_KEY=your_anthropic_key_here
# HUGGINGFACE_API_TOKEN=your_hf_token_here
EOF
        print_warning "Created .env file with placeholders. Please update with your actual API keys."
    else
        print_info ".env file already exists"
    fi
}

# Main setup function
main() {
    echo "MASEE Environment Setup"
    echo "======================"
    echo ""

    check_python
    create_venv
    install_dependencies
    create_directories
    check_files
    create_env_file

    echo ""
    print_success "Environment setup completed!"
    echo ""
    print_info "To activate the virtual environment, run:"
    echo "  source masee_env/bin/activate    # On Linux/Mac"
    echo "  masee_env\\Scripts\\activate         # On Windows"
    echo ""
    print_info "To run a single experiment:"
    echo "  ./scripts/run_experiment.sh -m gpt-4o-mini -e base -p 100 -d car -s 3"
    echo ""
    print_info "To run batch experiments:"
    echo "  ./scripts/run_batch_experiments.sh"
    echo ""
    print_warning "Don't forget to update the .env file with your API keys!"
}

# Show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -h, --help      Show this help message"
    echo ""
    echo "This script will:"
    echo "  1. Check for Python 3.7+"
    echo "  2. Create a virtual environment"
    echo "  3. Install required dependencies"
    echo "  4. Create directory structure"
    echo "  5. Check for configuration files"
    echo "  6. Create sample .env file"
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
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

# Run main setup
main