from smolagents import CodeAgent, TaskStep, ActionStep
import json


instruction_prompt = """
# Role:
You are a reasoning agent responsible for evaluating the quality of a provided answer to a customer inquiry. Your goal is to ensure the answer is **clear, precise, and fully addresses the customer's needs** without unnecessary length or excessive details. The focus is on **effectiveness rather than just comprehensiveness**.

# Task:
- Given a sequence of memory steps containing **observations and model-generated outputs**, along with a final answer, determine if the answer is **optimal**—meaning it is **accurate, concise, and directly answers the customer's concerns**.
- If the answer is **incorrect, incomplete, or unclear**, set `"decision": "fail"` and provide a `"reason"` explaining why.
- If the answer is **technically correct but could be improved**, also set `"decision": "fail"`, and include a `"refine_query"` with suggestions for improvement.
- Refinements in `"refine_query"` should focus on:
  - Improving clarity, conciseness, or relevance.
  - Correcting missing or inaccurate details.
  - Enhancing readability and logical flow.
  - Adding useful but minimal additional insights if necessary.

# Considerations:
- The **goal is to find the best possible answer, not just the longest or most detailed one**.
- The answer should be **concise yet fully informative**, avoiding excessive elaboration.
- `"decision": "fail"` should be assigned **only if the answer has meaningful gaps, inaccuracies, or could be significantly improved**.
- `"decision": "pass"` should be assigned if the answer is **well-structured, accurate, and provides exactly what the customer needs**.

# Pass Criteria:
`"decision": "pass"` should be assigned if the answer:
- **Directly addresses** all relevant observations from memory.
- Is **clear, concise, and well-structured**.
- Avoids unnecessary elaboration but still provides **all essential details**.
- Is phrased in a way that minimizes the need for further clarification.

# Failure Criteria:
`"decision": "fail"` must be assigned if:
- The answer **does not fully address the customer's inquiry**.
- The response contains **vague, misleading, or incomplete information**.
- The wording could be **significantly improved for clarity or impact**.
- It includes **irrelevant information** that detracts from the main point.

# Input:
{}

# Output:
{{
    "decision": "<pass/fail>",
    "reason": "<clear and balanced explanation of why the answer is incorrect, incomplete, or suboptimal>",
    "refine_query": "<concise and actionable recommendations for improvement>"
}}
"""


refinement_prompt = """
Improve the previous answer based on the following feedback.
Instruction and question: {}
Reason for failure: {}  
Required refinements: {}  

Generate a new, improved answer that fully addresses these issues.
"""


class ReasoningAgent:
    def __init__(self, model, prompt: str = instruction_prompt):
        self.prompt = prompt
        self.model = model

    def filter(self, step) -> dict:
        """Extract relevant attributes from a step."""
        list_att = ['model_output', 'observations']
        return {key: step.dict().get(key) for key in list_att}

    def forward(self, meta_agent: CodeAgent, answer: str) -> dict:
        """Evaluate if the answer sufficiently meets the observations."""
        memory = meta_agent.memory.steps
        filtered_memory = [self.filter(step) for step in memory]

        reasoning_answer = {
            'memory': filtered_memory,
            'answer': answer
        }

        prompt = self.prompt.format(json.dumps(reasoning_answer, indent=4))
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
    #TODO:
    - làm vòng for step_num
    - cho meta agent trả lời, sau đó cho dùng reasoning đánh giá
    - nếu decision không ngon, thì feedback lại meta, kèm với reason + refine query
    """

    def loop(self, prompt, meta_agent: CodeAgent, step_num: int = 10) -> dict:
        """Run reasoning in a loop if needed (placeholder for iteration logic)."""
        final_answer = meta_agent.run(prompt)

        response = self.forward(meta_agent, final_answer)
        if response['decision'] == 'pass':
            return final_answer
        else:
            for i in range(step_num):
                # define prompt and task
                task_prompt = refinement_prompt.format(prompt, response['reason'], response["refine_query"])
                task = TaskStep(task=task_prompt)
                # append for doing task
                meta_agent.memory.steps.append(task)
                # define action
                print(f'ACTION: {i}')
                action = ActionStep()
                # get answer
                final_answer = meta_agent.step(action)
                # append action to memory
                meta_agent.memory.steps.append(task)
                response = self.forward(meta_agent, final_answer)
                if response['decision'] == 'pass':
                    break
        return final_answer       
if __name__ == '__main__':
    pass
