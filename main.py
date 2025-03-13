import argparse
from io import BytesIO
from time import sleep
import pandas as pd
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
import json
from smolagents import CodeAgent, DuckDuckGoSearchTool, MultiStepAgent, tool, ToolCallingAgent
from smolagents.agents import ActionStep
from smolagents.tools import Tool
from langchain_community.agent_toolkits.sql.base import create_sql_agent
from langchain_community.utilities import SQLDatabase
from langchain_openai import ChatOpenAI
from agents.web_agent import initialize_agent, initialize_driver
from smolagents.cli import load_model
from utils import load_config, save_config, create_folder, init_ques_folder, load_experiment_config, load_jsonl
from agents.product_agent import RVSQLAgentCalling
from agents.qastorage_agent import get_qa_agent
from agents.vectorstore import load_vector_store
from agents.qastorage_agent import QAVectorSearchCalling, PVectorSearchCalling, AVectorSearchCalling
import os
import jsonlines
import datetime
import sys
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

DATA_CHOICE = 'pants'
'''
CONFIG
'''
# load the config file for experiment
experiment_config_dir, experiment_config = load_experiment_config()

# create datetime for make different folder experiments
date_time = f'_{datetime.datetime.now().strftime("%Y-%m-%d %H-%M-%S").__str__()}'
experiment_config['datetime'] = date_time

# # extract the part for get validation data and make prediction file
# model_name, _type, part = sys.argv[1], sys.argv[2], int(sys.argv[3])

# print(sys.argv)

if len(sys.argv) != 4:
    print("Usage: python main.py <value>")
    sys.exit(1)
# part = int(sys.argv[1])
# print(f'PART: {part}')
model_name, _type, part = sys.argv[1], sys.argv[2], int(sys.argv[3])
print(model_name)
experiment_config['model'] = model_name
experiment_config['model'] = experiment_config['model'].replace(
    '.', '-').replace(':', '-')
experiment_config['name'] = _type
experiment_config['agent'] = [_type]
experiment_config['part'] = part
experiment_config['model-id'] = model_name
# part = experiment_config['part']

save_config(experiment_config_dir, experiment_config)
# log folder
log_dir = "log"

# create name for experiment folder
experiment_name = experiment_config['name'] + "_" + \
    experiment_config['model'] + experiment_config['datetime']

# create folder
experiment_folder = create_folder(
    os.path.join(log_dir, experiment_name, str(experiment_config['part'])))
# experiment_config['part'] = part
save_config(experiment_config_dir, experiment_config)

create_folder(
    f"D:/AI_CODE/MASEE/data/{experiment_config['model']}/{experiment_config['name']}")


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Run a multi-agent system to answer product-related questions.")
    parser.add_argument(
        "model_name",
        type=str,
        default='model',
        nargs="?",
    )
    parser.add_argument(
        "_type",
        type=str,
        default='type',
        nargs="?",
    )
    parser.add_argument(
        "part",
        type=str,
        default='part',
        nargs="?",
    )
    parser.add_argument(
        "prompt",
        type=str,
        nargs="?",  # Makes it optional
        default="what's the weather in New York?",
        help="The prompt to run with the agent",
    )
    parser.add_argument(
        "--question_df_path",
        type=str,
        default=f"D:/AI_CODE/MASEE/data/{DATA_CHOICE}_pqa_validation_part{experiment_config['part']}.csv",
        help="Path to the question dataframe CSV file",
    )
    parser.add_argument(
        "--save_path",
        type=str,
        default=f"D:/AI_CODE/MASEE/data/{experiment_config['model']}/{experiment_config['name']}/{DATA_CHOICE}_predictions_part{experiment_config['part']}_{experiment_name}.jsonl",
        help="Path to save the evaluation predictions",
    )
    return parser.parse_args()


pqa_instructions = """
Answer a product-related question from a user interacting with an e-commerce platform. You will be given user question and the product details. There are two types of questions: yes-no and WH.
Use your knowledge in the shopping domain or using your equipped tools to answer the question.
Remember to plan to answer efficiently because some tools are very expensive. Be concise and explain your answer to the user.
Example question:
- Question: Will these shrink after a wash?
- Question-type: yes-no
- Product :
    - title: Dickies Men’s Jeans, 100% Cotton.
    - asin: xxyy - this is very important as can be used for querying the database.
    - description: This is a product description
\n\n
User Question:
{}
\n
- question_id: {}
- question_type: {}
Product Details:
- asin: {}
- title: {}
- description: {}
"""
load_dotenv()

config = load_config('path_config.yaml')
args = parse_arguments()

rv_db = SQLDatabase.from_uri(f"sqlite:///{config['data']['review_db']}")
q_db = load_vector_store(config['data']['q_faiss_index'])
d_db = load_vector_store(config['data']['d_faiss_index'])


def web_ag(config):
    global driver
    web_ag_config = load_config(config['web_agent'])
    driver = initialize_driver(config=web_ag_config)

    web_agent = initialize_agent(config=web_ag_config)
    web_agent.python_executor("from helium import *", web_agent.state)
    return web_agent


def product_agent():
    return RVSQLAgentCalling()


def QAStorageAgent():
    return get_qa_agent()


def evaluation(
    question_df: pd.DataFrame,
    meta_agent: CodeAgent = None,
    model=None,
    save_path: str = '',
):
    """
    Chạy đánh giá trên question_df và lưu từng kết quả vào file .jsonl ngay sau khi hoàn thành một dòng.
    """
    list_prev_key = []
    if experiment_config['part'] == 6 and 'prev_file' in experiment_config:
        print('CONTINUE')
        prev_file = experiment_config['prev_file']
        list_jsonl = load_jsonl(prev_file)
        list_prev_key = [list(value.keys())[0] for value in list_jsonl]
    with jsonlines.open(save_path, mode='a') as writer:
        for _, row in question_df.iterrows():

            '''
            save current question for experiment so that other file can get the current question folder
            '''
            if row['question_id'] in list_prev_key:
                print('SKIP QUESTION')
                continue
            experiment_config['cur_ques'] = row['question_id']
            save_config(experiment_config_dir, experiment_config)

            # create question folder
            path = os.path.join(experiment_folder,
                                experiment_config['cur_ques'])
            ques_folder = create_folder(path)

            # create file for question folder
            init_ques_folder(ques_folder)
            description = ''
            if experiment_config['agent'] != None:
                if experiment_config['agent'][0] in ['base_description', 'base_description_code', 'qa']:
                    description = row['description']
                    print('DESCRIPTION INCLUDED!')
            prompt = pqa_instructions.format(
                row['question_text'], row['question_id'], row['question_type'], row['asin'], row['item_name'], description)
            q_doc, d_doc = q_db.get_by_ids(
                [row['question_id']]), d_db.get_by_ids([row['asin']])
            q_db.delete(ids=[row['question_id']])
            d_db.delete(ids=[row['asin']])

            related_ques = [doc.id for doc in q_db.similarity_search("", k=q_db.index.ntotal)
                            if doc.metadata.get("asin") == row['asin']]

            print(related_ques)
            # Xóa các câu hỏi có cùng `asin` khỏi FAISS
            if related_ques:
                q_docs_backup = q_db.get_by_ids(related_ques)
                print(
                    f"REMOVING {len(related_ques)} questions with asin={row['asin']}")
                q_db.delete(ids=related_ques)
            if isinstance(meta_agent, CodeAgent):
                predicted_answer = meta_agent.run(prompt)
            else:
                predicted_answer = model(
                    messages=[{'content': prompt, 'role': 'user'}]
                ).content

            q_db.add_documents(q_doc)
            d_db.add_documents(d_doc)
            q_db.add_documents(q_docs_backup)
            # write new line
            writer.write({row['question_id']: predicted_answer})
            break
    print(f"Saved results to {save_path}")


def write_json(data, path):
    with open(path, "a", encoding="utf-8") as file:
        file.write(json.dumps(data, ensure_ascii=False) + "\n")


def main():
    # sql_agent_rv = create_sql_agent(
    #     llm=ChatOpenAI(model="gpt-4o-mini", temperature=0),
    #     db=rv_db,
    #     agent_type="openai-tools",
    #     verbose=True
    # )

    # qa_agent = get_qa_agent()
    meta_agent_config = load_config(config['meta_agent'])
    meta_agent_config['model-id'] = experiment_config['model-id']
    save_config(config['meta_agent'], meta_agent_config)
    # cut prod agent
    tools = []
    manage = []
    if experiment_config['agent'] is not None:
        if ('web' in experiment_config['agent']):
            web_agent = web_ag(config)
            manage.append(web_agent)
        if ('qa' in experiment_config['agent']):
            tools.append(QAVectorSearchCalling())
            tools.append(PVectorSearchCalling())
            tools.append(AVectorSearchCalling())
        if ('product' in experiment_config['agent']):
            prod_agent = product_agent()
            tools.append(prod_agent)
    print(manage)
    print(tools)
    meta_agent = CodeAgent(
        tools=tools,
        model=load_model(
            meta_agent_config['model-type'], meta_agent_config['model-id'], meta_agent_config['model-api'], meta_agent_config['api-key'], meta_agent_config['api-base']),
        managed_agents=manage,
        additional_authorized_imports=['time', 'numpy', 'pandas']
    )

    model = load_model(meta_agent_config['model-type'], meta_agent_config['model-id'],
                       meta_agent_config['model-api'], meta_agent_config['api-key'], meta_agent_config['api-base'])
    model_choice = meta_agent
    if experiment_config['agent'][0] in ['base', 'base_description']:
        model_choice = model
        print('CHOOSE TEXT MODEL')
    question_df = pd.read_csv(args.question_df_path)
    prediction = evaluation(
        question_df, meta_agent=model_choice, save_path=args.save_path)


if __name__ == "__main__":
    main()
