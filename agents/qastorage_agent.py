import argparse
from io import BytesIO
from time import sleep
from typing import Dict, Optional, List
import yaml
import helium
from dotenv import load_dotenv
from PIL import Image
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from langchain_community.agent_toolkits.sql.base import create_sql_agent
from smolagents import CodeAgent, DuckDuckGoSearchTool, MultiStepAgent, tool, ToolCallingAgent
from smolagents.agents import ActionStep
from smolagents.cli import load_model
from smolagents.memory import ActionStep, AgentMemory, PlanningStep, SystemPromptStep, TaskStep, ToolCall
from smolagents.monitoring import (
    YELLOW_HEX,
    AgentLogger,
    LogLevel,
)
from collections import deque
from langchain_community.utilities import SQLDatabase
from langchain_openai import ChatOpenAI
# from vectorstore import create_vector_store, load_vector_store, save_vector_store
from agents.vectorstore import create_vector_store, load_vector_store, save_vector_store

from smolagents.tools import Tool

from sentence_transformers import CrossEncoder

import json
import os

from utils import load_experiment_config, write_json


def load_config(yaml_path):
    with open(yaml_path, "r") as stream:
        try:
            return yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
            return {}


q_db = load_vector_store("D:/AI_CODE/MASEE/data/q_faiss_index")
d_db = load_vector_store("D:/AI_CODE/MASEE/data/d_faiss_index")


experiment_config_dir, experiment_config = load_experiment_config()

dir_qa = os.path.abspath(os.path.join(
    "log", experiment_config['name'], "qa.jsonl"))
dir_pqa = os.path.abspath(os.path.join(
    "log", experiment_config['name'], "product_qa.jsonl"))
reranker = CrossEncoder(
    "jinaai/jina-reranker-v1-turbo-en", trust_remote_code=True)

class QAVectorSearchCalling(Tool):
    name = "qa_vector"
    description = """calls the vector database to retrieve most similar questions to the input question. The tool can be used
    to search for similar questions, or other creative use cases. Provide user question (or your refinement of the question) to search for similar questions."""
    inputs = {"query": {"type": "string", "description": "The text query to perform. must contain product asin"},
              "k": {"type": "integer", "description": "The number of similar questions to return", "nullable": True}}
    output_type = "string"

    def forward(self, query: str, k: int = 50) -> str:
        ans = q_db.similarity_search(query, k)
        out = {
            "type": "QA-Embedding-Retrieve",
            "query": query,
            "retrieve": [value.__str__() for value in ans],
            "top_k": k,
        }
        write_json(out, dir_qa)
        return ans.__str__()


class PVectorSearchCalling(Tool):
    name = "product_vector"
    description = """calls the vector database to retrieve most similar products to the input product. The tool can be used
    to search for similar products, or other creative use cases, such as retrieve similar products and see their question-answer pairs,etc. Provide product description (or your refinement) as the input"""
    inputs = {"query": {"type": "string", "description": "The text query to perform. must contain product asin"},
              "k": {"type": "integer", "description": "The number of similar products to return, should be at least 50", "nullable": True},
              "rank": {"type": "integer", "description": "the top similar products after reranking, should be less than 10", "nullable": True}}
    output_type = "string"

    def forward(self, query: str, k: int = 50, rank: int = 5) -> str:
        ans = d_db.similarity_search(query, k)
        if k < rank:
            rank = k
        print(f"k: {k}, rank: {rank}")
        ans_str = [value.__str__() for value in ans]
        reranker_res = reranker.rank(
            query, ans_str, return_documents=True, top_k=rank)
        print(f"reranker_res: {reranker_res}")
        out = {
            "type": "P-Embedding-Retrieve",
            "query": query,
            "retrieve": ans_str,
            "rerank": [value.__str__() for value in reranker_res],
            "top_k": k,
            "rank": rank,
        }
        write_json(out, dir_pqa)
        if ("rerank" in experiment_config['agent']):
            return reranker_res.__str__()
        return ans.__str__()


retriever_instructions = """
\n
Remember to validate retrieved results by comparing them to the user question and the product details, 
This is typical in the e-commerce domain when users ask questions about products without specifying the product details. Think creatively to answer get the answer.\n
"""


def get_qa_agent():
    config = load_config('config/product_agent.yaml')
    return ToolCallingAgent(
        tools=[QAVectorSearchCalling(), PVectorSearchCalling()],
        model=load_model(config['model-type'], config['model-id']),
        planning_interval=8,
        name="QA_Vector_Search_Agent",
        description="""
        Search for similar questions and / or similar products (with answered questions) to the input question. This agent can use reasoning to generate a chain of queries to retrieve most
        similar questions and products to the input question, as well as analyze output to return the user answer directly if possible. Often this should be call first because it's cheap.
        """,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run a multi-agent system to answer product-related questions.")
    parser.add_argument(
        "prompt",
        type=str,
        nargs="?",  # Makes it optional
        default="Product: Dickies Men’s Jeans, 100% Cotton. Will this Jean shrink after a wash?",
        help="The prompt to run with the agent",
    )

    args = parser.parse_args()

    config = load_config('config/product_agent.yaml')
    qastr_agent = ToolCallingAgent(
        tools=[QAVectorSearchCalling(), PVectorSearchCalling()],
        model=load_model(config['model-type'], config['model-id']),
        planning_interval=20,

    )
    qastr_agent = get_qa_agent()
    fin_answer = qastr_agent.run(retriever_instructions + args.prompt)
    print(fin_answer)
