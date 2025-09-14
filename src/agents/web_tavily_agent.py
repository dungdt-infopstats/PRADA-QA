from smolagents.tools import Tool
from typing import Dict, Optional, List
import yaml
import json
import os
from utils import load_experiment_config, write_json
import pandas as pd
from tavily import TavilyClient


experiment_config_dir, experiment_config = load_experiment_config()
DATA_CHOICE = experiment_config['data_choice']

list_api_key = [
    "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",
    "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",
    "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",
    "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",
    "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",
    "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",
    "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",
    "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"
]
def load_config(yaml_path):
    with open(yaml_path, "r") as stream:
        try:
            return yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
            return {}
        
    

class TavilySearch(Tool):
    name = "search"
    description = """Performs a tavily web search based on your query (think a Google search) then returns the top search results."""
    inputs = {"query": {"type": "string", "description": "The search query to perform."}}
    output_type = "string"

    def __init__(self, min_score = 0):
        super().__init__()
        self.min_score = min_score

    def forward(self, query: str) -> str:
        experiment_config_dir, experiment_config = load_experiment_config()

        experiment_name = experiment_config['name'] + "_" + \
            experiment_config['model'] + experiment_config['datetime']
        
        dir_tavily = os.path.abspath(os.path.join("log", experiment_name, str(experiment_config['part'])))

        dir_ques = f"data/{DATA_CHOICE}_pqa_validation_part{experiment_config['part']}.csv"

        question_df = pd.read_csv(dir_ques)

        question_id = experiment_config['cur_ques']

        ques = question_df[question_df['question_id'] == question_id]['question_text'].values[0]
        title = question_df[question_df['question_id'] == question_id]['item_name'].values[0]

        file_path = os.path.join(
            dir_tavily, experiment_config['cur_ques'], 'tavily.jsonl')
        print(f"Saving to {file_path}")


        count = 0
        while count < len(list_api_key) * 2:
            try:
                api_key = list_api_key[count%len(list_api_key)]
                tavily_client = TavilyClient(api_key)

                input_query = f"""ITEM NAME: {title}\n QUESTION: {ques}\n ADDITIONAL QUERY: {query}"""
                if len(input_query) > 400:
                    input_query = f"QUESTION: {ques}\n ADDITIONAL QUERY: {query}"
                
                if len(input_query) > 400:
                    input_query = f"ADDITIONAL QUERY: {query}"
                response = tavily_client.search(
                    query=input_query,
                    search_depth="advanced"
                )
                print('QUERY:' + response['query'])
                # if response['']
                break
            except Exception as e:
                print(e)
                print('Change API!')
                count += 1
        if count >= len(list_api_key)*2:
            raise Exception('All API are not available')
        print("RESPONSE: " + response['results'].__str__())
        ans = []
        for result in response['results']:
            if result['score'] >= int(self.min_score):
                ans.append(
                    f'''
                    TITLE: {result['title']}, CONTENT: {result['content']}
                    '''
                )
    
        if len(ans) == 0:
            ans.append('There is no reliable information, you should retrieve information from other source')

        out = {
            "type": "Tavily",
            "question": ques,
            "query": query,
            "raw_rensponse": response,
            "answer": ans
        }

        try:
            return_val = ans.__str__()
        finally:
            write_json(out, file_path)
            return return_val