from smolagents import CodeAgent, TaskStep, ActionStep
import json


instruction_prompt = """
You are an evaluator responsible for assessing whether an agent's response correctly answers a user's question based on the retrieved observations. Your goal is to ensure:
1. The response directly answers the user’s question (not off-topic or misleading).  
2. The response is explainable and based on factual information from the provided observations.  
3. The observations retrieved are relevant to the question and sufficiently support the response.  
4. The response should be well-structured, logically sound, and persuasive.  


Evaluation Criteria
Pass if all conditions are met:  
- The response correctly addresses the question without going off-topic.  
- The response is factually accurate and explainable based on the retrieved observations.  
- The observations align with the question's intent and provide relevant supporting data.  
- The response is logically structured and persuasive.
- The response includes the reason why it response this.

Fail if any of these occur:  
- The response does not correctly answer the question or is off-topic.  
- The response is not properly explained or lacks factual support, evidences.
- The retrieved observations do not provide relevant information for the question.  
- The response is misleading, incomplete, or contradicts the observations.  
- More verification is needed, such as using external tools like web search.
- The observation is too short or nothing or just include none, which means the system lacks of analytics.

Decision Process
1. Check if the response actually answers the user’s question.  
2. Verify if the response is factually supported by the retrieved observations.  
3. Ensure the observations are relevant and sufficient for answering the question.  
4. Make sure the answer includes enough evidences.
4. Score the response based on clarity, correctness, and factual grounding.  

Scoring System:  
- 9-10: Excellent - Completely relevant, well-explained, factually solid.  
- 7-8: Good - Mostly correct but may lack some detail.  
- 5-6: Average - Some issues with clarity or missing key facts.  
- 3-4: Poor - Major gaps in explanation or relevance.  
- 1-2: Fail - Off-topic, misleading, or factually incorrect. 

Output Format
{{ "decision": "pass" | "fail", "score": <integer from 1 to 10>, "reason": "<Explain why the response is marked pass or fail>", "refine_query": "<Suggest refinements, such as retrieving different information using web search or querying additional sources. The agent which answers questions already has tool for retrieve similar question, similar product>" }}


Examples

Example 1 (Pass - High Score)
Question: "Does this phone have wireless charging?"*
Observations: "Supports wireless charging via Qi standard.", "Charging speed up to 15W for wireless mode."  
Answer: "Yes, this phone supports wireless charging using the Qi standard, as mentioned in the product specifications."

Evaluation Output:
{{
  "decision": "pass",
  "score": 9,
  "reason": "The response directly answers the question, is factually correct, and is well-explained.",
  "refine_query": "No refinement needed."
}}

Example 2 (Fail - Off-topic Answer)
Question: "Does this phone have wireless charging?"
Observations: "Supports wireless charging via Qi standard.", "Charging speed up to 15W for wireless mode."
Answer: "This phone has a long battery life and a fast processor, making it great for gaming."

Evaluation Output:
{{
  "decision": "fail",
  "score": 2,
  "reason": "The response does not answer the question. It discusses battery life and processor speed instead of wireless charging.",
  "refine_query": "Ensure the response directly addresses the question about wireless charging. No additional query is needed, as the provided observations already contain the relevant information."
}}

Example 3 (Fail - Answer Not Aligned with Observations)
Question: "Does this phone have wireless charging?"
Observations: "Supports wireless charging via Qi standard.", "Charging speed up to 15W for wireless mode."
Answer: "No, this phone does not support wireless charging, but it has fast wired charging."

Evaluation Output:
{{
  "decision": "fail",
  "score": 3,
  "reason": "The response contradicts the provided observations, which clearly state that the phone supports wireless charging.",
  "refine_query": "Ensure that the response correctly interprets the observations. Verify the information in the product specifications if needed."
}}

Example 4 (Fail - Observations Not Relevant)
Question: "Does this phone have wireless charging?"
Observations: "This phone features a 120Hz display with HDR support.", "Equipped with a triple-lens camera system."
Answer: "Yes, this phone supports wireless charging using the Qi standard."

Evaluation Output:
{{
  "decision": "fail",
  "score": 4,
  "reason": "The response claims wireless charging support, but the provided observations do not contain any relevant information about this feature.",
  "refine_query": "Retrieve information specifically about wireless charging support, such as checking product specifications or using web search."
}}

Question: {}
Observations: {}
Answers: {}
"""

refinement_prompt = """
{} 
- reason: {}
- refinements: {}
"""


class ReasoningAgent:
    def __init__(self, model, prompt: str = instruction_prompt):
        self.prompt = prompt
        self.model = model

    def filter(self, step) -> dict:
        """Extract relevant attributes from a step."""
        list_att = ['observations']
        return {key: step.dict().get(key) for key in list_att}

    def forward(self, meta_agent: CodeAgent, question: str, answer: str) -> dict:
        """Evaluate if the answer sufficiently meets the observations."""
        memory = meta_agent.memory.steps
        filtered_memory = [self.filter(step) for step in memory]
        print(filtered_memory)
        reasoning_answer = {
            'question': question,
            'observations': filtered_memory[:-1],
            'answer': answer
        }

        prompt = self.prompt.format(reasoning_answer['question'], reasoning_answer['observations'].__str__(), reasoning_answer['answer'])
        print(prompt)
        messages = [{'content': prompt, 'role': 'user'}]

        response = self.model(messages).content

        try:
            response_dict = json.loads(response)
            if not all(key in response_dict for key in ["decision", "reason", "refine_query"]):
                raise ValueError("Response missing required keys")
        except (json.JSONDecodeError, ValueError) as e:
            response_dict = {
                "decision": "fail",
                "reason": "Invalid model response format",
                "refine_query": "Ensure the model returns a valid JSON structure"
            }

        return response_dict

    """
    TODO:
    - làm vòng for step_num
    - cho meta agent trả lời, sau đó cho dùng reasoning đánh giá
    - nếu decision không ngon, thì feedback lại meta, kèm với reason + refine query
    """
    def loop_no_reasoning(self, prompt, meta_agents) -> dict:
        """Run reasoning in a loop if needed (placeholder for iteration logic)."""
        prompt_2 = 'You must call tools at the first step to get the answer! ALso, your answer must include evidences!'
        prompt_3 = 'ALso, your answer must include detail evidences!'
        meta_agent = meta_agents[0]
        meta_agent0 = meta_agents[1]

        final_answer = meta_agent0.run(prompt + prompt_2 + prompt_3, reset=True)

        #copy memory from agent0 to agent
        meta_agent.memory = meta_agent0.memory
        meta_agent.state = meta_agent0.state
        meta_agent.step_number = meta_agent0.step_number
        final_answer = meta_agent.run(prompt, reset=False)
        return final_answer

    def loop(self, prompt, question, meta_agents, step_num: int = 3) -> dict:
        """Run reasoning in a loop if needed (placeholder for iteration logic)."""
        prompt_2 = 'You must call tools at the first step to get the answer!' 
        prompt_3 = 'ALso, your answer must include detail evidences!'
        meta_agent = meta_agents[0]
        meta_agent0 = meta_agents[1]

        final_answer = meta_agent0.run(prompt + prompt_2 + prompt_3, reset=True)

        #copy memory from agent0 to agent
        meta_agent.memory = meta_agent0.memory
        meta_agent.state = meta_agent0.state
        meta_agent.step_number = meta_agent0.step_number
        # final_answer = meta_agent.run(prompt, reset = True)

        response = self.forward(meta_agent, question, final_answer)
        print(f'RESPONSE {0}: {response}')
        if response['decision'] == 'pass':
            return final_answer
        else:
            for i in range(step_num):
                # define prompt and task
                task_prompt = refinement_prompt.format(
                    prompt, response['reason'], response["refine_query"])
                final_answer = meta_agent.run(task_prompt + prompt_3, reset=False)
                # task = TaskStep(task=task_prompt)
                # # append for doing task
                # meta_agent.memory.steps.append(task)
                # # define action
                # print(f'ACTION: {i}')
                # action = ActionStep()
                # # get answer
                # final_answer = meta_agent.step(action)
                # # append action to memory
                # meta_agent.memory.steps.append(task)
                response = self.forward(meta_agent, question, final_answer)
                print(f'RESPONSE {i+1}: {response}')
                if response['decision'] == 'pass':
                    break
        return final_answer


if __name__ == '__main__':
    pass
