import json
import jsonlines
import yaml
import pandas as pd
from openai import OpenAI
from camel.agents import ChatAgent
from pydantic import BaseModel
from typing import List
import os

DATA_DIR = "/teamspace/studios/this_studio/MASEE/data"
SCORES_PATH = os.path.join(DATA_DIR, "scores/eval_scores_phi-4_no_des-part_poster1_from_des_cpr.json")
QUESTION_CSV_PATH = os.path.join(DATA_DIR, "acs_pqa_validation_part_poster1.csv")
EVAL_BASE_PATH = os.path.join(DATA_DIR, "eval/base_part_poster1_microsoft/phi-4_no_des.jsonl")


def load_config(yaml_path):
    with open(yaml_path, "r") as stream:
        try:
            return yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
            return {}


def get_response(prompt, model="gpt-4o-mini"):
    response = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model=model,
    ).choices[0].message.content
    
    return json.loads(response)  # parse to JSON
    

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


eval_accuracy_instructions = """
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

Users answers: {}
AI answer: {}

Your answer:\n

"""


# profiling llm as a user to judge the AI model answer. If the answer is not helpful, return 0. If the answer is helpful, return 1. The helpfulness
# is detertimine by the explainability, fact-based like real feedbacks from buyers, product descriptions, or other sources of information. If the answer does not satisfies
# the these previous requirements, it must because the model cannot find supporting information to answer, and in that case it must admit it and give recommendation to the user
# on how to get the answer from other sources, etc. In this case return 0.5. The final response should be a strict JSON format.

eval_consensus_instructions = """
You are an online marketplace user evaluating an AI assistant's response to your product-related question.

Your task is to assess the AI's answer for helpfulness based on:

Explainability

Use of factual information (e.g., real buyer feedback, product descriptions, credible sources)

Provide a score as follows:

1: Helpful (answer is clear, informative, and supported by factual details and most importantly, must match what user ask for)

0.5: Partially helpful (AI admits inability to provide details and recommends alternative ways to find the information)

0: Not helpful (answer lacks clarity, factual support, or is incorrect)

Note that AI models tend to give answers based on common knowledge when the product description is not detailed enough. In that case, the score should be 0.5 if the answer is persuasive, or 0 if it's too general.

Your evaluation must strictly follow this JSON format with three keys: question_id, comment, and score.
- question_id: the ID of the question
- comment: your brief justification for the score. This first involves understanding of the question to get what user want, then the justification of the AI answer.
- score: the score of the AI answer
{{
    "question_id": "xxxx",
    "comment": "This answer is general for one product type, which might not help as the user want to know a specific property of the product",
    "score": 0
}}

Use the following information to evaluate:

Your question: {question_text}
Question ID: {question_id}

Product Information:

Product Title: {item_name}

Product Description: {description}

AI's Answer: {ai_answer}

Your response:

"""

class ConsensusFormatResponse(BaseModel):
    question_id: str
    comment: str
    score: float


def merge():
    with open(SCORES_PATH, 'r') as f:
        data = json.load(f)
    
    question_df = pd.read_csv(QUESTION_CSV_PATH)
    
    with jsonlines.open(EVAL_BASE_PATH, "r") as f:
        ai_answers = {list(obj.keys())[0]: obj[list(obj.keys())[0]] for obj in f}
    
    for _, row in question_df.iterrows():
        q_id = row.question_id
        data[q_id].update({
            'question_type': row.question_type,
            'question_text': row.question_text,
            'item_name': row.item_name,
            'description': row.description,
            'user_answers': row.answers,
            'answer_aggregated': None if pd.isna(row.answer_aggregated) else row.answer_aggregated,
            'ai_answer': ai_answers.get(q_id, "")
        })
    
    with open(SCORES_PATH, 'w') as f:
        json.dump(data, f, indent=4)


def eval_scores():
    question_df = pd.read_csv(QUESTION_CSV_PATH)
    with jsonlines.open(EVAL_BASE_PATH) as reader:
        answers = {list(obj.keys())[0]: obj[list(obj.keys())[0]] for obj in reader}
    
    scores = {}
    for _, row in question_df.iterrows():
        prompt = eval_accuracy_instructions.format(
            row.question_id, row.question_type, row.question_text, row.item_name, row.description, str(row.answers), answers.get(row.question_id, "")
        )
        scores[row.question_id] = get_response(prompt)
    
    return scores

def eval_infer_from_des():
    question_df = pd.read_csv(QUESTION_CSV_PATH)
    with jsonlines.open(EVAL_BASE_PATH) as reader:
        answers = {list(obj.keys())[0]: obj[list(obj.keys())[0]] for obj in reader}
    
    scores = {}
    for _, row in question_df.iterrows():
        prompt = eval_inferfrom_des.format(
            row.question_id, row.question_text, row.item_name, row.description, answers.get(row.question_id, "")
        )
        scores[row.question_id] = get_response(prompt)
    
    return scores

def eval_consensus():
    agent = ChatAgent(system_message="")
    question_df = pd.read_csv(QUESTION_CSV_PATH)
    with jsonlines.open(EVAL_BASE_PATH) as reader:
        answers = {list(obj.keys())[0]: obj[list(obj.keys())[0]] for obj in reader}
    
    scores = {}
    for _, row in question_df.iterrows():
        inputs = {
            "question_text": row.question_text,
            "question_id": row.question_id,
            "item_name": row.item_name,
            "description": row.description,
            "ai_answer": answers.get(row.question_id, "")
        }
        prompt = eval_consensus_instructions.format(**inputs)
        response = agent.step(prompt, response_format=ConsensusFormatResponse).msgs[0].content
        scores[row.question_id] = json.loads(response)
    
    return scores
        
if __name__ == "__main__":
    client = OpenAI()
    # scores = eval_scores()
    # scores = eval_consensus()
    scores = eval_infer_from_des()
    # print(get_response("What is the best laptop for gaming?"))
    sum_score = sum([score['score'] for score in scores.values()])
    print(f"Total score: {sum_score}/{len(scores)}, Accuracy: {sum_score/len(scores)}")
    with open(SCORES_PATH, "w") as f:
        json.dump(scores, f)
    merge()

    # test_ai_answer = {
    #     "question_id": "Tx3HX7P5VPNHHGO",
    #     "question_type": "WH",
    #     "question_text": "How do you install this hanging hardware there are no instructions?",
    #     "item_name": "SIGNFORD Framed Canvas Home Artwork Decoration Nordic Style Abstract Color Canvas Wall Art for Living Room, Bedroom - 24x36 inches",
    #     "description": "Multiple Sizes Floating frame wrap canvas prints,multiple sizes and frame colors optional,you can choose the most suitable one according to the request. High Definition Printed High definition picture, photo prints on thick high quality canvas to create the look and feel of the original nature and masterpiece. This canvas is water-resistant and fade-resistant, stretched and stapled to durable shrink resistant frames. Attention to Detail Our in-house design team is constantly checking the quality and detail of every artwork, we provide to ensure an excellently produced product for whatever occasion you need them for. We Stand by Our Products We are native US factory, all of our products are made by professionals and ship fast.Just try our framed canvas wall art, a decoration for your bedroom, living room, kitchen etc, or a perfect gift choice for your family, friends,etc.\nBullet points: [Premium Quality]-High quality printed canvas stretched and stapled to durable shrink resistant frames,made in and shipped from the USA.\n[Widely Application]-Perfect decoration choice for living room,bedroom,office,hotel,bathroom,dining room,kitchen,bar etc.\n[Ideal Wall Art]-A creative gift to your family and friends in birthday,wedding,anniversary,thanksgiving day and other festivals.\n[Easy to Hang]-Package is wrapped and membrane covering,hanging accessory kit included.\n[Note]-Due to monitor display issues, actual colors maybe slightly different from the pictures.",
    #     "ai_answer": {
    #         "reasoning": "The product description mentions that an 'hanging accessory kit is included' under the 'Easy to Hang' section. This implies that the product comes with the necessary hardware and possibly some basic instructions for installation. While specific step-by-step instructions are not provided in the description, the inclusion of a hanging accessory kit suggests that the installation process should be straightforward. Therefore, the absence of explicit instructions does not indicate that installation is difficult or impossible.", 
    #     "answer": "The product includes a hanging accessory kit, which should make installation straightforward even without explicit instructions."}
    # }

    # test_ai_answer["ai_answer"] = json.dumps(test_ai_answer["ai_answer"])

    
    # agent = ChatAgent(
    #     system_message= ""
    # )

    # response = agent.step(eval_consensus_instructions.format(**test_ai_answer), response_format=ConsensusFormatResponse)
    
    # print(response.msgs[0].content)

    print("Done")