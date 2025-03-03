import argparse
from io import BytesIO
from time import sleep
from collections import deque
from logging import getLogger
from typing import Any, Callable, Dict, Generator, List, Optional, Set, Tuple, Union
import helium
from dotenv import load_dotenv
from PIL import Image
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import yaml
from smolagents import CodeAgent, DuckDuckGoSearchTool, MultiStepAgent, tool, ToolCallingAgent
from smolagents.agents import ActionStep
from smolagents.tools import Tool
from langchain_community.agent_toolkits.sql.base import create_sql_agent
from langchain_community.utilities import SQLDatabase
from langchain_openai import ChatOpenAI
from smolagents.cli import load_model
from agents.vectorstore import create_vector_store, load_vector_store, save_vector_store


def load_config(yaml_path):
    with open(yaml_path, "r") as stream:
        try:
            return yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
            return {}


rv_db = SQLDatabase.from_uri("sqlite:///D:/AI_CODE/MASEE/data/acs_review.db")
sql_agent_rv = create_sql_agent(llm=ChatOpenAI(model="gpt-4o-mini", temperature=0), db=rv_db,agent_type="openai-tools", verbose = True)

class RVSQLAgentCalling(Tool):
    name = "review_database"
    description = """calls the SQL agent to execute a query in the User Review database. This contains all reviews of users on products, rating, and other information. The tool can be used
    to search for reviews, rating... of products, or other creative use cases. Remember to provide asin of the product you want to search for.
    The SQL Agent can take a text request for information,
    then use reasoning to generate a chains of SQL queries to answer the question.
    - example of call: 
    ```py
    product_issues = review_database(query="B003MABXY issues or not working")
    ```<end_code>
    """
    inputs = {"query": {"type": "string", "description": "The text query to perform. must contain product asin, along with the information you want to retrieve"}}
    output_type = "string"

    def forward(self, query: str) -> str:
        return sql_agent_rv.invoke(query)
    


def initialize_product_agent(config: Dict[str, Any]) -> CodeAgent:
    product_agent = ToolCallingAgent(
        tools=[RVSQLAgentCalling()],
        model=load_model(config['model-type'], config['model-id']),
    )
    return product_agent


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Run a multi-agent system to answer product-related questions.")
    parser.add_argument(
        "prompt",
        type=str,
        nargs="?",  # Makes it optional
        default= "Summarize review on the product asin: B00001WQIY. Give your opinion on the product. Is it worth buying?",
        help="The prompt to run with the agent",
    )


    args = parser.parse_args()

    product_agent = initialize_product_agent(load_config('config/product_agent.yaml'))
    product_agent.run(args.prompt)