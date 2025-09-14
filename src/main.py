"""Main entry point for MASEE experiments."""

import argparse
import os
import sys
import pandas as pd
from dotenv import load_dotenv

# Add project root and src to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)
sys.path.insert(0, src_path)

# Add masee env smolagents to path (custom modified version)
masee_site_packages = os.path.join(project_root, 'masee', 'Lib', 'site-packages')
if os.path.exists(masee_site_packages):
    sys.path.insert(0, masee_site_packages)
    print(f"[INFO] Using custom smolagents from: {masee_site_packages}")

from core.experiment import ExperimentManager, validate_arguments
from core.evaluation import EvaluationEngine
from core.agent_factory import AgentFactory
from agents.vectorstore import load_vector_store
from utils.config import load_config
from utils.file_operations import create_folder

# Configure UTF-8 encoding
sys.stdout.reconfigure(encoding='utf-8')
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

# Load environment variables
load_dotenv()

# PQA Instructions template
PQA_INSTRUCTIONS = """
Answer a product-related question from a user on an e-commerce platform. You will be provided with a user question and product details. There are two types of questions: yes-no and WH.
Use your knowledge of the shopping domain or available tools to answer accurately. Optimize your approach as some tools may be costly. Be concise while explaining your answer to the user.
Your response will be verified by another agent. If your answer does not meet the required standards, the agent will mark it as failed. Additionally, they will provide a reason and suggestions for improvement in the Reflection section.
Carefully analyze the Reflection section to refine your next response. Pay close attention to the reason and refinements provided.
If the retrieval information from other tool is seem not helpful, you must call other tool to retrieve more reliable information.

Example question:
- Question: Will these shrink after a wash?
- Question-type: yes-no
- Product :
    - title: Dickies Men's Jeans, 100% Cotton.
    - asin: xxyy - this is very important as can be used for querying the database.
    - description: This is a product description

User Question:
{}

- question_id: {}
- question_type: {}
Product Details:
- asin: {}
- title: {}
- description: {}

Reflection:
"""


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Run a multi-agent system to answer product-related questions."
    )
    parser.add_argument("model_name", type=str, help="Model name to use")
    parser.add_argument("experiment_type", type=str, help="Type of experiment")
    parser.add_argument("part", type=int, help="Experiment part number")
    parser.add_argument("data_choice", type=str, help="Data choice (e.g., 'car', 'acs')")
    parser.add_argument("step", type=str, help="Number of steps")
    parser.add_argument(
        "--question_df_path", type=str, help="Path to question dataframe CSV"
    )
    parser.add_argument(
        "--save_path", type=str, help="Path to save evaluation predictions"
    )
    return parser.parse_args()


def main():
    """Main execution function."""
    # Validate arguments
    validate_arguments(sys.argv, 6)

    # Parse arguments
    model_name, experiment_type, part, data_choice, step = (
        sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4], sys.argv[5]
    )

    print(f"Running experiment with model: {model_name}")
    print(f"Experiment type: {experiment_type}")
    print(f"Part: {part}, Data choice: {data_choice}, Steps: {step}")

    # Setup experiment
    experiment_manager = ExperimentManager()
    experiment_manager.setup_experiment(
        model_name=model_name,
        experiment_type=experiment_type,
        part=part,
        data_choice=data_choice,
        step=step
    )

    # Get experiment configuration
    experiment_config = experiment_manager.get_experiment_config()
    experiment_name = experiment_manager.get_experiment_name()
    experiment_folder = experiment_manager.get_experiment_folder()

    # Load path configuration
    config = load_config('path_config.yaml')

    # Setup data paths
    question_df_path = f"data/{data_choice}_pqa_validation_part{part}.csv"
    save_path = (
        f"data/{experiment_config['model']}/{experiment_config['name']}/"
        f"{data_choice}_predictions_part{part}_{experiment_name}.jsonl"
    )

    # Load vector stores only if needed (not for base experiments or demo data)
    q_db, d_db, a_db = None, None, None
    if experiment_type != 'base' and data_choice != 'demo':
        print("Loading vector stores...")
        try:
            q_db = load_vector_store(f"data/q_faiss_index_{data_choice}")
            d_db = load_vector_store(f"data/d_faiss_index_{data_choice}")
            a_db = load_vector_store(f"data/attribute_faiss_index_{data_choice}")
            print("Vector stores loaded successfully")
        except Exception as e:
            print(f"Warning: Could not load vector stores: {e}")
            print("Continuing without vector stores...")

    # Create agent factory and agents
    print("Creating agents...")
    agent_factory = AgentFactory(config, experiment_config)

    if 'base' in experiment_config['agent']:
        model_choice = agent_factory.create_base_model()
        print('USING BASE TEXT MODEL')
    else:
        model_choice = agent_factory.create_meta_agents()
        print('USING META AGENTS')

    # Set max steps
    if isinstance(model_choice, list):
        print(f'SET MAX STEP: {step}')
        model_choice[0].max_steps = int(step)

    # Load question data
    print(f"Loading questions from: {question_df_path}")
    question_df = pd.read_csv(question_df_path)

    # Setup evaluation engine
    evaluation_engine = EvaluationEngine(
        experiment_config=experiment_config,
        experiment_config_dir=experiment_manager.config_dir,
        experiment_name=experiment_name,
        experiment_folder=experiment_folder
    )

    # Run evaluation
    print("Starting evaluation...")
    evaluation_engine.run_evaluation(
        question_df=question_df,
        meta_agents=model_choice,
        save_path=save_path,
        pqa_instructions=PQA_INSTRUCTIONS
    )

    print("Evaluation completed!")


if __name__ == "__main__":
    main()