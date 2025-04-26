import json
import jsonlines
import yaml
import pandas as pd
from openai import OpenAI
from dotenv import load_dotenv
import os
import numpy as np
from bert_score import score as bert_score_fn
import numpy as np

import ast

def extract_answer_texts(answers_raw):
    if isinstance(answers_raw, str):
        try:
            # Chuyển từ string sang list[dict] nếu đúng định dạng
            answers_list = ast.literal_eval(answers_raw)
        except Exception:
            return [answers_raw]
    elif isinstance(answers_raw, list):
        answers_list = answers_raw
    else:
        return [str(answers_raw)]

    # Trích ra các answer_text
    cleaned = []
    for item in answers_list:
        if isinstance(item, dict) and "answer_text" in item:
            cleaned.append(item["answer_text"])
        else:
            cleaned.append(str(item))
    return cleaned

def load_config(yaml_path):
    with open(yaml_path, "r") as stream:
        try:
            return yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
            return {}

def load_experiment_config(config_dir = "config/experiment.yaml"):
    experiment_config_dir = load_config(config_dir)['dir']
    experiment_config = load_config(experiment_config_dir)
    return experiment_config_dir, experiment_config

def load_jsonl(filename):
    with open(filename, 'r', encoding='utf-8') as file:
        return [json.loads(line) for line in file]

def save_config(yaml_path, yaml_data):
    yaml_file = yaml.dump(yaml_data)
    with open(yaml_path, "w", encoding="utf-8") as file:
        file.write(yaml_file)

def create_folder(path):
    os.makedirs(path, exist_ok=True)
    return path

def init_ques_folder(path):
    files = ['web.jsonl', 'qa.jsonl', 'product_qa.jsonl', 'product_sql.jsonl', 'att.jsonl']
    for file in files:
        file_dir = os.path.join(path, file)
        with open(file_dir, 'w'):
            pass


def write_json(data, path):
    with open(path, "a", encoding="utf-8") as file:
        file.write(json.dumps(data, ensure_ascii=False) + "\n")
    return

import re

def process_text(text, index):
    # Chỉ giữ lại các chữ cái (A-Z, a-z) và dấu cách
    text = re.sub(r'[^A-Za-z\s]', '', text)
    
    # Chuyển thành danh sách các từ
    words = text.split()
    
    # Lấy 5000 từ cuối cùng nếu có đủ
    if index < 0:
        sampling_words = words[index:]
    else: 
        sampling_words = words[:index]
    return " ".join(sampling_words)

def get_observation(file_name, part, ques_id):
    prefix = f"acs_predictions_part{part}_"
    name = file_name.removeprefix(prefix)
    observation = []
    path = f"log/{name}/{part}/{ques_id}/"
    print(name)
    if os.path.exists(path + "observation.jsonl"):
        with open(path + "observation.jsonl", "r", encoding="utf-8") as f:
            data = [json.loads(line) for line in f]
        observation = process_text(data[0]['observation'], -5000)
    else:
        files = [entry.name for entry in os.scandir(path) if entry.is_file()]
        for file in files:
            with open(path + file, "r", encoding="utf-8") as f:
                observation.append([json.loads(line) for line in f])
        observation = process_text(observation.__str__(), 5000)
    return observation

import time
def get_response(prompt, model="gpt-4o-mini"):
    response = client.chat.completions.create(
        messages=[{
            "role": "user",
            "content": prompt,
        }],
        model=model,
    ).choices[0].message.content
    time.sleep(1)
    # parse to json
    print(response)
    response = json.loads(response)
    return response

def calculate_bertscore(predicts, references, lang='vi', agg_method='max'):
    precisions, recalls, f1s = [], [], []

    for pred, refs in zip(predicts, references):
        preds_rep = [pred] * len(refs)
        P, R, F1 = bert_score_fn(preds_rep, refs, lang=lang, verbose=False)

        if agg_method == 'max':
            precisions.append(P.max().item())
            recalls.append(R.max().item())
            f1s.append(F1.max().item())
        elif agg_method == 'mean':
            precisions.append(P.mean().item())
            recalls.append(R.mean().item())
            f1s.append(F1.mean().item())
        else:
            raise ValueError("agg_method phải là 'max' hoặc 'mean'")

    return np.array(precisions), np.array(recalls), np.array(f1s)


# eval_instructions = """
# You are given a user question on e-commerce products and a set of answers: other user answers along with the answer from an AI system.
# There are two types of questions: yes-no and WH. Although the yes-no questions are straightforward,  it is not always the case that the answer is a simple yes or no.
# Your task is to compare AI answers with other user answers and give the score: 1 if the AI answer match ideas / information in other user answers (including partial match), 0 if totally different, 0.5 if it is really hard to decide.
# Remember to consider the context of the question and the product details.

# Return your response in a dictionary format (JSON) with three keys: question_id, score, and comment. Only return json format, not include any character at the start of output.
# Example
# {{
#     "question_id": xxxx,
#     "score": 1
#     "comment": "The AI answer is very similar to the user answers. It is a good answer."
# }}

# User Question:
# - question_id: {}
# - question_type: {}
# - question_text: {}
# - product_title: {}
# - product_description: {}
# - answer_aggregated: {}

# Users answers: {}
# AI answer: {}

# Your answer:\n

# """

eval_instructions = """
You are given a user question on e-commerce products and a set of answers: other user answers along with the answer from an AI system.
Your task is to compare AI answers with other user answers and give the score: 1 if the AI answer match ideas of majority of users, else give the score 0.
Return your response in a dictionary format (JSON) with three keys: question_id, score, and comment. Only return json format, not include any character at the start of output.
Example
{{
    "question_id": xxxx,
    "score": 1
    "comment": "The AI answer is very similar to the user answers. It is a good answer."
}}
User Question:
- question_id: {}
- question_text: {}

Users answers: {}
AI answer: {}

Your answer:\n
"""

eval_inferfrom_des = """
You are given a user's question about an e-commerce product and the AI model answer for that question. You will evaluate and give score to the answer: 1 - if the answer
can be directly infered from product description (plus it's title) and directly resolve user's question, 0 otherwise. Be conscious as AI models generally hallucinate by using common sense
or not directly answer user inquiry. Be concise, the answer deserves a score of 1 only if it correctly utilizes the product description and get what user need (not by any other medium).


Return your response in a dictionary format with three keys: question_id, score, and comment.
Example:
{{
    "question_id": xxxx,
    "score": 1
    "comment": "The AI answer is very similar to the user answers. It is a good answer."
}}

User Question:
- question_id: {}
- question_text: {}
- product_title: {}
- product_description: {}

AI answer: {}

Your response:\n
"""

eval_user_consensus_instructions = """
You are given a user's question about an e-commerce product and the AI model answer for that question. You will be acting as a user and judge the AI model answer.
Score the answer from 0 or 1 based on:
1: The answer is helpful and informative, objective,  providing clear and relevant information like details about the product, other userss' feedback, or other sources of information (e.g., Internet)
0.1 to 0.9: The answer is partially helpful, it is subjective and does not provide detailed explanation of the answer. It may be based on common knowledge or general information, but lacks specific details about the product or user feedback. Dependent on the degree of helpfulness, the score can vary from 0.1 to 0.9.
0: The answer is not helpful, lacks clarity, or is incorrect. It does not provide any useful information to the user.

Return your response in a dictionary format with three keys: question_id, score, and comment.

Example :
{{
    "question_id": xxxx,
    "score": 1
    "comment": "The AI answer is based on various sources of information, including the product description and some previous buyers' feedback. The agreement between both product description and user feedback is strong, making the answer very helpful."
}}
;
{{
    "question_id": yyyy,
    "score": 0.3
    "comment": "The AI answer is based on general knowledge of jeans, but it does not provide strong evidence from the specific product, which may be inaccurate. In general e-commerce platforms, what users want is the specific product information, as shop owners can lie about the product. The answer is not very helpful."
}}
;
{{
    "question_id": zzzz,
    "score": 0
    "comment": "The AI answer is not helpful and lacks clarity. It does not provide any useful information to the user."

}}


User Question:
question_id: {}
question_text: {}
product_title: {}
product_description: {}
observation: {}

AI answer: {}

Your response:

"""


# def eval_scores(part, prediction_dir, type_eval):
#     question_df = pd.read_csv(
#         f"data/acs_pqa_validation_part{part}.csv")
#     with jsonlines.open(prediction_dir) as reader:
#         answers = {}
#         for obj in reader:
#             q_id = list(obj.keys())[0]
#             answers[q_id] = obj[q_id]

#     scores = {}

#     for row in question_df.iterrows():
#         row = row[1]
#         # prompt = eval_instructions.format(row.question_id, row.question_type, row.question_text,
#         #                                   row.item_name, row.description, row.answer_aggregated, str(row.answers), answers.get(row.question_id, ""))
#         if type_eval == "user":
#             prompt = eval_instructions.format(row.question_id, row.question_text, str(row.answers), answers.get(row.question_id))
#         elif type_eval == "des":
#             prompt = eval_inferfrom_des.format(row.question_id, row.question_text, row.item_name, row.description, answers.get(row.question_id))
#         print(prompt)
#         scores[row.question_id] = get_response(prompt)
#     return scores

def eval_scores(part, prediction_dir, type_eval, name):
    question_df = pd.read_csv(f"data/acs_pqa_validation_part{part}.csv")
    with jsonlines.open(prediction_dir) as reader:
        answers = {list(obj.keys())[0]: list(obj.values())[0] for obj in reader}

    scores = {}

    for row in question_df.itertuples(index=False):
        q_id = row.question_id
        ai_answer = answers.get(q_id, "")

        if type_eval == "user":
            prompt = eval_instructions.format(q_id, row.question_text, str(row.answers), ai_answer)
            references = extract_answer_texts(row.answers)
        elif type_eval == "des":
            prompt = eval_inferfrom_des.format(q_id, row.question_text, row.item_name, row.description, ai_answer)
            references = [f"{row.description}"]
        elif type_eval == "observation":
            observation = get_observation(name,part,q_id)
            prompt = eval_user_consensus_instructions.format(q_id, row.question_text, row.item_name, row.description, observation, ai_answer)
        else:
            continue
        print(prompt)
        try:
            gpt_result = get_response(prompt)
        except Exception as e:
            print(f"GPT error for {q_id}: {e}")
            gpt_result = {"question_id": q_id, "score": 0, "comment": "GPT error"}
        if type_eval in ['user', 'des']:
            # Tính BERTScore
            try:
                P_max, R_max, F1_max = calculate_bertscore([ai_answer], [references], agg_method='max')
                bert_p_max, bert_r_max, bert_f1_max = round(P_max[0], 4), round(R_max[0], 4), round(F1_max[0], 4)
                P_mean, R_mean, F1_mean = calculate_bertscore([ai_answer], [references], agg_method='mean')
                bert_p_mean, bert_r_mean, bert_f1_mean = round(P_mean[0], 4), round(R_mean[0], 4), round(F1_mean[0], 4)
            except Exception as e:
                print(f"BERTScore error for {q_id}: {e}")
                bert_p_max, bert_r_max, bert_f1_max = 0.0, 0.0, 0.0
                bert_p_mean, bert_r_mean, bert_f1_mean = 0.0, 0.0, 0.0
            # Thêm vào kết quả
            gpt_result.update({
                "bertscore_max_precision": bert_p_max,
                "bertscore_max_recall": bert_r_max,
                "bertscore_max_f1": bert_f1_max,
                "bertscore_mean_precision": bert_p_mean,
                "bertscore_mean_recall": bert_r_mean,
                "bertscore_mean_f1": bert_f1_mean
            })
        
        scores[q_id] = gpt_result
    return scores




def temp_merge(eval_dir, prediction_dir):
    with open(eval_dir, 'r') as f:
        data = json.load(f)
    question_df = pd.read_csv(
        f"data/acs_pqa_validation_part{part}.csv")
    with jsonlines.open(prediction_dir) as reader:
        ai_answers = {}
        for obj in reader:
            q_id = list(obj.keys())[0]
            ai_answers[q_id] = obj[q_id]
    for row in question_df.iterrows():
        # data[row[1].question_id] = {'question_type': row[1].question_type,
        #                          'question_text': row[1].question_text,
        #                          'user_answers': row[1].answers,
        #                          'ai_answer': ai_answers.get(row[1].question_id, "")}
        data[row[1].question_id]['question_type'] = row[1].question_type
        data[row[1].question_id]['question_text'] = row[1].question_text
        data[row[1].question_id]['user_answers'] = row[1].answers
        data[row[1].question_id]['product_description'] = row[1].description
        data[row[1].question_id]['ai_answer'] = ai_answers.get(row[1].question_id, "")

    # save to file
    with open(eval_dir, 'w') as f:
        json.dump(data, f)


if __name__ == "__main__":
    path = "config/experiment.yaml"
    eval_config_dir = load_config(path)['eval_dir']
    eval_config = load_config(eval_config_dir)

    parts = eval_config['part']
    names = eval_config['name']
    type_evals = eval_config['type']
    all_score = []
    count = 0
    for type_eval in type_evals:
        for part, name in zip(parts, names):
            experiment_config_dir, experiment_config = load_experiment_config(path)

            prediction_dir = f"data/{experiment_config['model']}/{experiment_config['name']}/{name}.jsonl"

            eval_path = f"data/{experiment_config['model']}/eval_{experiment_config['name']}"

            eval_dir = os.path.join(eval_path, f'eval_{type_eval}_{name}.json')
            create_folder(eval_path)
            load_dotenv()
            client = OpenAI()
            scores = eval_scores(part=part, prediction_dir=prediction_dir, type_eval=type_eval, name=name)
            # print(get_response("What is the best laptop for gaming?"))
            sum_score = sum([score['score'] for score in scores.values()])
            all_score.append(sum_score)
            print(f"Total score: {sum_score}/{len(scores)}")
            # Tính trung bình các chỉ số BERTScore
            if type_eval in ['user', 'des']:
                bert_p_max_all = [v["bertscore_max_precision"] for v in scores.values()]
                bert_r_max_all = [v["bertscore_max_recall"] for v in scores.values()]
                bert_f1_max_all = [v["bertscore_max_f1"] for v in scores.values()]
                bert_p_mean_all = [v["bertscore_mean_precision"] for v in scores.values()]
                bert_r_mean_all = [v["bertscore_mean_recall"] for v in scores.values()]
                bert_f1_mean_all = [v["bertscore_mean_f1"] for v in scores.values()]

                print(f"BERTScore max: P={np.mean(bert_p_max_all):.4f}, R={np.mean(bert_r_max_all):.4f}, F1={np.mean(bert_f1_max_all):.4f}")
                print(f"BERTScore mean: P={np.mean(bert_p_mean_all):.4f}, R={np.mean(bert_r_mean_all):.4f}, F1={np.mean(bert_f1_mean_all):.4f}")

            with open(eval_dir, "w") as f:
                json.dump(scores, f)
            temp_merge(eval_dir=eval_dir, prediction_dir=prediction_dir)
            print("Done")
            print(all_score)
