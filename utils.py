import json
import jsonlines
import yaml
import pandas as pd
from openai import OpenAI
from dotenv import load_dotenv
import os


def load_config(yaml_path):
    with open(yaml_path, "r") as stream:
        try:
            return yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
            return {}

def load_experiment_config(config_dir = "config\experiment.yaml"):
    experiment_config_dir = load_config(config_dir)['dir']
    experiment_config = load_config(experiment_config_dir)
    return experiment_config_dir, experiment_config


def save_config(yaml_path, yaml_data):
    yaml_file = yaml.dump(yaml_data)
    with open(yaml_path, "w", encoding="utf-8") as file:
        file.write(yaml_file)

def create_folder(path):
    os.makedirs(path, exist_ok=True)
    return path

def init_ques_folder(path):
    files = ['web.jsonl', 'qa.jsonl', 'product_qa.jsonl', 'product_sql.jsonl']
    for file in files:
        file_dir = os.path.join(path, file)
        with open(file_dir, 'w'):
            pass
            

def get_response(prompt, model="gpt-4o-mini"):
    response = client.chat.completions.create(
        messages=[{
            "role": "user",
            "content": prompt,
        }],
        model=model,
    ).choices[0].message.content

    # parse to json
    response = json.loads(response)
    return response


eval_instructions = """
You are given a user question on e-commerce products and a set of answers: other user answers along with the answer from an AI system.
There are two types of questions: yes-no and WH. Although the yes-no questions are straightforward,  it is not always the case that the answer is a simple yes or no.
Your task is to compare AI answers with other user answers and give the score: 1 if the AI answer match ideas / information in other user answers (including partial match), 0 if totally different, 0.5 if it is really hard to decide.
Remember to consider the context of the question and the product details.

Return your response in a dictionary format with three keys: question_id, score, and comment.
Example
{{
    "question_id": xxxx,
    "score": 1
    "comment": "The AI answer is very similar to the user answers. It is a good answer."
}}

User Question:
- question_id: {}
- question_type: {}
- question_text: {}
- product_title: {}
- product_description: {}
- answer_aggregated: {}

Users answers: {}
AI answer: {}

Your answer:\n

"""

part = 8
type = 'retrieve'
cut = ''

prediction_dir = f"D:/AI_CODE/MASEE/data/predictions_part{part}_{type}_{cut}.jsonl"
eval_dir = f'D:/AI_CODE/MASEE/data/eval_scores_{part}_{type}_{cut}.json'
def eval_scores():
    question_df = pd.read_csv(
        f"D:/AI_CODE/MASEE/data/acs_pqa_validation_part{part}.csv")
    with jsonlines.open(prediction_dir) as reader:
        answers = {}
        for obj in reader:
            q_id = list(obj.keys())[0]
            answers[q_id] = obj[q_id]

    scores = {}

    for row in question_df.iterrows():
        row = row[1]
        prompt = eval_instructions.format(row.question_id, row.question_type, row.question_text,
                                          row.item_name, row.description, row.answer_aggregated, str(row.answers), answers.get(row.question_id, ""))
        print(prompt)
        scores[row.question_id] = get_response(prompt)
    return scores


def temp_merge():
    with open(eval_dir, 'r') as f:
        data = json.load(f)
    question_df = pd.read_csv(
        f"D:/AI_CODE/MASEE/data/acs_pqa_validation_part{part}.csv")
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
        data[row[1].question_id]['ai_answer'] = ai_answers.get(row[1].question_id, "")

    # save to file
    with open(eval_dir, 'w') as f:
        json.dump(data, f)


if __name__ == "__main__":
    load_dotenv()
    client = OpenAI()
    scores = eval_scores()
    # print(get_response("What is the best laptop for gaming?"))
    sum_score = sum([score['score'] for score in scores.values()])
    print(f"Total score: {sum_score}/{len(scores)}")
    with open(eval_dir, "w") as f:
        json.dump(scores, f)
    temp_merge()
    print("Done")
