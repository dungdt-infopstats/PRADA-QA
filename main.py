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
from smolagents.cli import load_model
from utils import load_config, save_config, create_folder, init_ques_folder, load_experiment_config, load_jsonl
from smolagents import LiteLLMModel

from agents.product_agent import RVSQLAgentCalling
# from agents.qastorage_agent import get_qa_agent
from agents.vectorstore import load_vector_store
from agents.reasoning_agent import ReasoningAgent
from agents.web_agent import initialize_agent, initialize_driver

import os
import jsonlines
import datetime
import sys

# reconfig to utf-8
sys.stdout.reconfigure(encoding='utf-8')

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

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
print(sys.argv)
if len(sys.argv) != 6:
    print("Usage: python main.py <value>")
    sys.exit(1)
# part = int(sys.argv[1])
# print(f'PART: {part}')
model_name, _type, part, data_choice, step = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4], sys.argv[5]
print(model_name)
experiment_config['model'] = model_name
experiment_config['model'] = experiment_config['model'].replace(
    '.', '-').replace(':', '-').replace('/','-')
experiment_config['name'] = _type
experiment_config['agent'] = _type.split('-')
experiment_config['part'] = part
experiment_config['model-id'] = model_name
experiment_config['data_choice'] = data_choice

DATA_CHOICE = data_choice
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
    f"data/{experiment_config['model']}/{experiment_config['name']}")


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
        "data_choice",
        type=str,
        default='data_choice',
        nargs="?",
    )
    parser.add_argument(
        "step",
        type=str,
        default='step',
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
        default=f"data/{DATA_CHOICE}_pqa_validation_part{experiment_config['part']}.csv",
        help="Path to the question dataframe CSV file",
    )
    parser.add_argument(
        "--save_path",
        type=str,
        default=f"data/{experiment_config['model']}/{experiment_config['name']}/{DATA_CHOICE}_predictions_part{experiment_config['part']}_{experiment_name}.jsonl",
        help="Path to save the evaluation predictions",
    )
    return parser.parse_args()


pqa_instructions = """
Answer a product-related question from a user on an e-commerce platform. You will be provided with a user question and product details. There are two types of questions: yes-no and WH.
Use your knowledge of the shopping domain or available tools to answer accurately. Optimize your approach as some tools may be costly. Be concise while explaining your answer to the user.
Your response will be verified by another agent. If your answer does not meet the required standards, the agent will mark it as failed. Additionally, they will provide a reason and suggestions for improvement in the Reflection section.
Carefully analyze the Reflection section to refine your next response. Pay close attention to the reason and refinements provided.
If the retrieval information from other tool is seem not helpful, you must call other tool to retrieve more reliable information.
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

Reflection:
"""
load_dotenv()

config = load_config('path_config.yaml')
args = parse_arguments()
rv_db = SQLDatabase.from_uri(f"sqlite:///{config['data']['review_db']}")
# q_db = load_vector_store(config['data']['q_faiss_index'])
# d_db = load_vector_store(config['data']['d_faiss_index'])


q_db = load_vector_store(f"D:/AI_CODE/MASEE/data/q_faiss_index_{DATA_CHOICE}")
d_db = load_vector_store(f"D:/AI_CODE/MASEE/data/d_faiss_index_{DATA_CHOICE}")
a_db = load_vector_store(f"D:/AI_CODE/MASEE/data/attribute_faiss_index_{DATA_CHOICE}")

def web_ag(config):
    global driver
    web_ag_config = load_config(config['web_agent'])
    driver = initialize_driver(config=web_ag_config)

    web_agent = initialize_agent(config=web_ag_config)
    web_agent.python_executor("from helium import *", web_agent.state)
    return web_agent


def product_agent():
    return RVSQLAgentCalling()


# def QAStorageAgent():
#     return get_qa_agent()


def evaluation(
    question_df: pd.DataFrame,
    meta_agents=None,
    model=None,
    save_path: str = '',
):
    """
    Chạy đánh giá trên question_df và lưu từng kết quả vào file .jsonl ngay sau khi hoàn thành một dòng.
    """
    list_prev_key = []
    if 'prev_file' in experiment_config:
        print('CONTINUE')
        prev_file = experiment_config['prev_file']
        list_jsonl = load_jsonl(prev_file)
        list_prev_key = [list(value.keys())[0] for value in list_jsonl]
    

    # REASONING_AGENT
    reasoning_model = LiteLLMModel(
        model_id='gpt-4o-mini'
    )
    reasoning_agent = ReasoningAgent(model = reasoning_model)


    count = 0
    with jsonlines.open(save_path, mode='a') as writer:
        for _, row in question_df.iterrows():
            count += 1
            print(count)

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
                if 'description' in experiment_config['agent']:
                    description = row['description']
                    print('DESCRIPTION INCLUDED!')
            prompt = pqa_instructions.format(
                row['question_text'], row['question_id'], row['question_type'], row['asin'], row['item_name'], description)
            q_doc, d_doc = q_db.get_by_ids(
                [row['question_id']]), d_db.get_by_ids([row['asin']])
            q_db.delete(ids=[row['question_id']])
            d_db.delete(ids=[row['asin']])
            
            if 'rmqa' in experiment_config['agent']:
                related_ques = [doc.id for doc in q_db.similarity_search("", k=q_db.index.ntotal)
                            if doc.metadata.get("asin") == row['asin']]

                print(related_ques)
            # Xóa các câu hỏi có cùng `asin` khỏi FAISS
            if 'rmqa' in experiment_config['agent']:
                print('IN RMQA')
                q_docs_backup = q_db.get_by_ids(related_ques)
                print(
                    f"REMOVING {len(related_ques)} questions with asin={row['asin']}")
                if len(related_ques) != 0:
                    q_db.delete(ids=related_ques)
            if type(meta_agents) == list:
                    try:
                        if 'reasoning' in experiment_config['agent']:
                            predicted_answer = reasoning_agent.loop(prompt=prompt, question=row['question_text'], meta_agents=meta_agents)
                        else:
                            if 'qafirst' in experiment_config['agent']:
                                predicted_answer = reasoning_agent.loop_no_reasoning(prompt = prompt, meta_agents= meta_agents)
                            else:
                                prompt_3 = 'ALso, your answer must include detail evidences!'
                                predicted_answer = meta_agents[0].run(prompt + prompt_3)
                        dir_log = os.path.abspath(os.path.join("log", experiment_name, str(experiment_config['part'])))
                        out = {
                            "observation": meta_agents[0].memory.steps.__str__()
                        }
                    except:
                        if 'reasoning' in experiment_config['agent']:
                            predicted_answer = reasoning_agent.loop(prompt=prompt, question=row['question_text'], meta_agents=meta_agents)
                        else:
                            if 'qafirst' in experiment_config['agent']:
                                predicted_answer = reasoning_agent.loop_no_reasoning(prompt = prompt, meta_agents= meta_agents)
                            else:
                                prompt_3 = 'ALso, your answer must include detail evidences!'
                                predicted_answer = meta_agents[0].run(prompt + prompt_3)
                        dir_log = os.path.abspath(os.path.join("log", experiment_name, str(experiment_config['part'])))
                        out = {
                            "observation": meta_agents[0].memory.steps.__str__()
                        }
                    file_path = os.path.join(dir_log, experiment_config['cur_ques'], 'observation.jsonl')
                    write_json(out, file_path)
            else:
                predicted_answer = meta_agents(
                    messages=[{'content': prompt, 'role': 'user'}]
                ).content        
            q_db.add_documents(q_doc)
            d_db.add_documents(d_doc)
            if 'rmqa' in experiment_config['agent']:
                if len(q_docs_backup) != 0:
                    q_db.add_documents(q_docs_backup)
            # write new line
            writer.write({row['question_id']: predicted_answer})
            q_doc = []
            q_docs_backup = []
    print(f"Saved results to {save_path}")


def write_json(data, path):
    with open(path, "a", encoding="utf-8") as file:
        file.write(json.dumps(data, ensure_ascii=False) + "\n")


def main():
    from agents.qastorage_agent import QAVectorSearchCalling, PVectorSearchCalling, AVectorSearchCalling
    from agents.web_tavily_agent import TavilySearch
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
    tools_2 = []
    manage = []
    if experiment_config['agent'] is not None:
        if ('web' in experiment_config['agent']):
            # web_agent = web_ag(config)
            # manage.append(web_agent)
            tools.append(DuckDuckGoSearchTool())
            # tools.append(VisitWebpageTool())
        if ('qav' in experiment_config['agent']):
            tools_2.append(QAVectorSearchCalling())
            tools.append(QAVectorSearchCalling())
        if 'desv' in experiment_config['agent']:
            tools_2.append(PVectorSearchCalling())
            tools.append(PVectorSearchCalling())
        if 'attv' in experiment_config['agent']:
            tools_2.append(AVectorSearchCalling())
            tools.append(AVectorSearchCalling())
        if ('product' in experiment_config['agent']):
            prod_agent = product_agent()
            tools.append(prod_agent)
        if ('webtv' in experiment_config['agent']):
            tools.append(TavilySearch())
    print(manage)
    print(tools)
    if 'plan' in experiment_config['agent']:
        meta_agent = ToolCallingAgent(
            tools=tools,
            model=load_model(
                meta_agent_config['model-type'], meta_agent_config['model-id'], meta_agent_config['model-api'], meta_agent_config['api-key'], meta_agent_config['api-base']),
            managed_agents=manage,
            # additional_authorized_imports=['time', 'numpy', 'pandas'],
            planning_interval=1,
        )

        meta_agent2 = ToolCallingAgent(
            tools=tools_2,
            model=load_model(
                meta_agent_config['model-type'], meta_agent_config['model-id'], meta_agent_config['model-api'], meta_agent_config['api-key'], meta_agent_config['api-base']),
            # additional_authorized_imports=['time', 'numpy', 'pandas'],
        )
    elif 'plancode' in experiment_config['agent']:
        meta_agent = CodeAgent(
            tools=tools,
            model=load_model(
                meta_agent_config['model-type'], meta_agent_config['model-id'], meta_agent_config['model-api'], meta_agent_config['api-key'], meta_agent_config['api-base']),
            managed_agents=manage,
            additional_authorized_imports=['time', 'numpy', 'pandas'],
            planning_interval=1
        )   

        meta_agent2 = CodeAgent(
            tools=tools_2,
            model=load_model(
                meta_agent_config['model-type'], meta_agent_config['model-id'], meta_agent_config['model-api'], meta_agent_config['api-key'], meta_agent_config['api-base']),
            additional_authorized_imports=['time', 'numpy', 'pandas'],
        )
    else:
        meta_agent = CodeAgent(
            tools=tools,
            model=load_model(
                meta_agent_config['model-type'], meta_agent_config['model-id'], meta_agent_config['model-api'], meta_agent_config['api-key'], meta_agent_config['api-base']),
            managed_agents=manage,
            additional_authorized_imports=['time', 'numpy', 'pandas'],
        )   

        meta_agent2 = CodeAgent(
            tools=tools_2,
            model=load_model(
                meta_agent_config['model-type'], meta_agent_config['model-id'], meta_agent_config['model-api'], meta_agent_config['api-key'], meta_agent_config['api-base']),
            additional_authorized_imports=['time', 'numpy', 'pandas'],
        )
    meta_agents = [meta_agent, meta_agent2]

    print(f'SET MAX STEP: {step}')
    meta_agents[0].max_steps = int(step)

    model = load_model(meta_agent_config['model-type'], meta_agent_config['model-id'],
                       meta_agent_config['model-api'], meta_agent_config['api-key'], meta_agent_config['api-base'])
    model_choice = meta_agents
    if 'base' in experiment_config['agent']:
        model_choice = model
        print('CHOOSE TEXT MODEL')
    question_df = pd.read_csv(args.question_df_path)
    prediction = evaluation(
        question_df, meta_agents=model_choice, save_path=args.save_path)


if __name__ == "__main__":
    main()
