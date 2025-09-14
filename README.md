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
- 🚀 Improves task fulfillment efficiency  
- 🛒 Tailored for Product Question Answering in e-commerce  
- 🤖 Built on LLM-powered multi-agent collaboration  
- ✅ Evaluated using reward models as human preference proxies  
- 📊 Demonstrates superior performance across multiple domains  

PRADA-QA sets a new direction for leveraging LLM-based multi-agent systems in e-commerce and beyond.

## 🏗️ Project Structure

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

## 🚀 Quick Start

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

3. **Test installation with demo**:
```bash
python run_demo.py
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

## ⚙️ Configuration

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

## 🎯 Available Commands

### Core Commands

| Command | Description | Example |
|---------|-------------|---------|
| `python src/main.py` | Run single experiment | `python src/main.py gpt-4o-mini base 100 demo 3` |
| `python run_demo.py` | Full workflow demonstration | `python run_demo.py` |

### Enhanced Script Commands

| Script | Description | Usage |
|--------|-------------|-------|
| `run_experiment.sh` | Enhanced single experiment with logging | `./scripts/run_experiment.sh --model gpt-4o-mini --type base --part 100` |
| `run_batch_experiments.sh` | Batch processing with parallel support | `./scripts/run_batch_experiments.sh --parallel --jobs 4` |
| `monitor_experiments.sh` | Real-time process monitoring | `./scripts/monitor_experiments.sh status --watch` |
| `analyze_results.py` | Comprehensive results analysis | `python scripts/analyze_results.py --visualize` |

### Testing Commands

| Command | Description |
|---------|-------------|
| `pytest` | Run all tests |
| `pytest tests/unit/` | Run unit tests only |
| `pytest tests/integration/` | Run integration tests |
| `./scripts/run_tests.sh` | Run tests with coverage report |

## 🤖 Agent Types

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

## 📊 Data Formats

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

## 🔍 Monitoring and Results

### Real-time Monitoring
```bash
# Check experiment status
./scripts/monitor_experiments.sh status

# Watch live progress with auto-refresh
./scripts/monitor_experiments.sh status --watch

# Monitor specific experiment log
./scripts/monitor_experiments.sh monitor experiment_log_file.txt

# Show system statistics
./scripts/monitor_experiments.sh stats
```

### Results Analysis
```bash
# Analyze specific experiment
python scripts/analyze_results.py results/experiment_name/

# Compare multiple experiments
python scripts/analyze_results.py --compare results/exp1/ results/exp2/

# Generate visual reports
python scripts/analyze_results.py --visualize --format html
```

## 🔧 Advanced Usage

### Batch Processing Configuration

The batch script automatically runs experiments with different combinations:

```bash
# Edit the script to modify experiment parameters
./scripts/run_batch_experiments.sh

# Run with parallel processing
./scripts/run_batch_experiments.sh --parallel --jobs 4

# Dry run to see planned experiments
./scripts/run_batch_experiments.sh --dry-run
```

### Custom Agent Development

1. **Create new agent** in `src/agents/`:
```python
from smolagents import CodeAgent

class CustomAgent(CodeAgent):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Custom initialization

    def process_query(self, query, context):
        # Custom processing logic
        return response
```

2. **Register in agent factory** (`src/core/agent_factory.py`)

3. **Add configuration support** in YAML files

### Environment Customization

The project uses a custom smolagents environment located in `masee/`. This allows for:
- Modified smolagents functionality
- Custom tool implementations
- Specialized agent behaviors

## 🧪 Testing

### Test Categories

1. **Unit Tests**: Test individual components
2. **Integration Tests**: Test complete workflows
3. **Performance Tests**: Test scalability and speed
4. **Smoke Tests**: Quick system verification

### Running Tests

```bash
# All tests
pytest

# Specific test categories
pytest tests/unit/
pytest tests/integration/
pytest tests/performance/

# With coverage report
./scripts/run_tests.sh
```

## 🚨 Troubleshooting

### Common Issues

1. **Import Errors**
   - Ensure custom smolagents path is correctly set
   - Check Python path in scripts

2. **API Key Issues**
   - Verify .env file contains correct keys
   - Check environment variable names match configuration

3. **Memory Issues**
   - Reduce batch size or dataset part size
   - Monitor with `./scripts/monitor_experiments.sh stats`

4. **Permission Issues**
   - Ensure script execution permissions: `chmod +x scripts/*.sh`

### Debug Mode

Enable detailed logging:
```bash
export MASEE_DEBUG=1
python src/main.py ...
```

### Verification Steps

1. **Test installation**: `python run_demo.py`
2. **Verify configuration**: Check YAML files in `config/`
3. **Test API keys**: Run a small experiment
4. **Check logs**: Review experiment log files

## 📈 Performance Tips

1. **Start small**: Use `part=50` for testing, scale up gradually
2. **Monitor resources**: Use monitoring scripts during long runs
3. **Use batch processing**: More efficient for multiple experiments
4. **Cache results**: System automatically caches to avoid reprocessing
5. **Parallel processing**: Use `--parallel` flag for batch runs

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Follow the existing code structure
4. Add tests for new functionality
5. Run the test suite: `pytest`
6. Update documentation
7. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📞 Support

### Getting Help

1. **First steps**: Run `python run_demo.py` to verify setup
2. **Check configuration**: Review files in `config/` directory
3. **Run tests**: Execute `pytest -v` to identify issues
4. **Check logs**: Review experiment log files for errors
5. **Monitor system**: Use `./scripts/monitor_experiments.sh stats`

### Documentation

- **Project structure**: See directory structure above
- **Configuration**: Check YAML files in `config/`
- **Examples**: Review `run_demo.py` for complete workflow
- **Testing**: See `TESTING_STATUS.md` for test coverage

---
