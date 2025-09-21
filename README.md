# PRADA-QA: Product QA with Multi-Agent Planning and Dynamic Knowledge Retrieval

## Overview
Large Language Model (LLM)-based autonomous agents have shown strong capabilities in decision-making and handling complex tasks. However, public research on applying multi-agent systems to **Product Question Answering (PQA)**—a crucial area in modern e-commerce—remains limited.

**PRADA-QA** is a framework designed to enhance the user experience through **multi-agent collaboration**, enabling dynamic information retrieval from diverse sources to respond to user queries accurately.

## Key Features
- **Multi-Agent Collaboration**: Agents work together to dynamically retrieve and integrate information for more accurate product-related responses.
- **Adaptive Planning Module**: Guides agents’ objectives adaptively, improving task fulfillment efficiency while minimizing redundant steps and operational costs.
- **Reward Model-Based Evaluation**: Uses a reward model (commonly applied in RLHF for LLMs) as a proxy for human preferences, ensuring user-centric quality in evaluation.
- **Generalizable Framework**: While designed for PQA, the evaluation and planning strategies may extend to other open-ended QA scenarios.

## Evaluation
- We employ a reward model-based evaluation strategy to capture user-centric quality.
- Experiments were conducted across **three distinct domains** to validate the framework’s effectiveness.
- Results show that **PRADA-QA outperforms traditional approaches**, delivering more accurate and contextually appropriate responses for PQA.

## Highlights
- Improves task fulfillment efficiency  
- Tailored for Product Question Answering in e-commerce  
- Built on LLM-powered multi-agent collaboration  
- Evaluated using reward models as human preference proxies  
- Demonstrates superior performance across multiple domains  

PRADA-QA sets a new direction for leveraging LLM-based multi-agent systems in e-commerce and beyond.

## Project Structure

```
MASEE/
├── src/                    # Core application code
│   ├── core/              # Core functionality
│   │   ├── experiment.py  # Experiment management
│   │   ├── evaluation.py  # Evaluation engine
│   │   └── agent_factory.py # Agent creation
│   ├── agents/            # Agent implementations
│   ├── utils/             # Utility functions
│   └── main.py           # Main entry point
├── config/                # Configuration files
│   ├── experiment/        # Experiment configurations
│   └── meta_agent.yaml   # Agent model configurations
├── data/                  # Dataset files
│   └── demo_pqa_validation_part*.csv
├── scripts/               # Automation scripts
│   ├── run_experiment.sh      # Single experiment runner
│   ├── run_batch_experiments.sh # Batch processing
│   ├── monitor_experiments.sh  # Monitoring tools
│   └── analyze_results.py     # Results analysis
├── tests/                 # Test suite
├── masee/                 # Custom smolagents environment
├── archive/               # Historical data and logs
└── legacy/                # Old code structure (ignored)
```

## Quick Start

### Prerequisites

- Python 3.10+
- Virtual environment (recommended)
- Required dependencies (see requirements.txt)

### Installation

1. **Clone and setup**:
```bash
git clone <repository-url>
cd MASEE
pip install -r requirements.txt
```

2. **Configure environment**:
```bash
# Copy and edit environment file
cp .env.example .env
# Edit .env with your API keys (OpenAI, Tavily, etc.)
```

### Running Your First Experiment

1. **Quick Demo** (recommended first step):
```bash
python run_demo.py
```

2. **Single Experiment**:
```bash
python src/main.py gpt-4o-mini base 100 demo 3
```

3. **Using Scripts** (recommended for production):
```bash
# Single experiment with enhanced features
./scripts/run_experiment.sh --model gpt-4o-mini --type base --part 100

# Batch experiments
./scripts/run_batch_experiments.sh

# Monitor running experiments
./scripts/monitor_experiments.sh status
```

## Configuration

### Experiment Configuration

Edit `config/experiment/multi_experiment.yaml`:
```yaml
agent: ['base', 'description']  # Agent types to use
model: 'gpt-4o-mini'           # Model identifier
name: 'experiment-name'         # Experiment name
part: 100                      # Dataset portion (questions to process)
```

### Model Configuration

Edit `config/meta_agent.yaml`:
```yaml
model-type: 'LiteLLMModel'     # Model type
model-id: 'gpt-4o-mini'        # Model identifier
model-api: 'OPENAI_API_KEY'    # API key environment variable
api-base: 'https://api.openai.com/v1'  # API base URL
```

## Agent Types

### Base Agent
- **Purpose**: Simple text-only evaluation
- **Use case**: Direct question-answer processing
- **Performance**: Fastest processing time
- **Best for**: Simple factual questions

### Web Agent
- **Purpose**: Uses web search for additional context
- **Features**: Tavily integration for real-time information
- **Use case**: Current product information, reviews
- **Performance**: Moderate speed, high accuracy

### Reasoning Agent
- **Purpose**: Multi-step reasoning approach
- **Features**: Advanced prompt engineering, chain-of-thought
- **Use case**: Complex analytical questions
- **Performance**: Slower but more thorough

### Description Agent
- **Purpose**: Uses product descriptions for context
- **Use case**: Specification-based questions
- **Performance**: Good balance of speed and accuracy

## Data Formats

### Input Data (CSV)
```csv
question_id,question_text,question_type,asin,item_name,description
Q001,What color is this product?,wh,ASIN001,Wireless Headphones,"High-quality wireless headphones with premium black finish..."
Q002,Is this waterproof?,yes-no,ASIN002,Sports Watch,"Durable sports watch with water-resistant casing..."
```

### Output Data (JSONL)
```json
{"Q001": "The product is black based on the description provided."}
{"Q002": "Yes, this product is water-resistant up to 50 meters."}
```
---
