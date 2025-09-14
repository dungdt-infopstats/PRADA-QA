"""Core evaluation functionality."""

import jsonlines
import os
import pandas as pd
from typing import Dict, Any, List, Union

from smolagents import LiteLLMModel
from agents.reasoning_agent import ReasoningAgent
from utils.config import save_config
from utils.file_operations import create_folder, init_ques_folder, write_json


class EvaluationEngine:
    """Main evaluation engine for running experiments."""

    def __init__(self, experiment_config: Dict[str, Any], experiment_config_dir: str,
                 experiment_name: str, experiment_folder: str):
        self.experiment_config = experiment_config
        self.experiment_config_dir = experiment_config_dir
        self.experiment_name = experiment_name
        self.experiment_folder = experiment_folder

        # Initialize reasoning agent
        reasoning_model = LiteLLMModel(model_id='gpt-4o-mini')
        self.reasoning_agent = ReasoningAgent(model=reasoning_model)

    def run_evaluation(self, question_df: pd.DataFrame, meta_agents: Union[List, Any],
                      save_path: str, pqa_instructions: str) -> None:
        """Run evaluation on question dataframe.

        Args:
            question_df: DataFrame containing questions
            meta_agents: Agent(s) to use for evaluation
            save_path: Path to save results
            pqa_instructions: Instructions for PQA task
        """
        # Handle previous results
        list_prev_key = self._get_previous_keys()

        count = 0
        with jsonlines.open(save_path, mode='a') as writer:
            for _, row in question_df.iterrows():
                count += 1
                print(f"Processing question {count}")

                # Skip if already processed
                if row['question_id'] in list_prev_key:
                    print('SKIP QUESTION')
                    continue

                # Setup question folder
                self._setup_question_folder(row['question_id'])

                # Prepare prompt
                description = self._get_description(row)
                prompt = pqa_instructions.format(
                    row['question_text'], row['question_id'], row['question_type'],
                    row['asin'], row['item_name'], description
                )

                # Process with agents
                predicted_answer = self._process_with_agents(
                    prompt, row, meta_agents
                )

                # Save results
                writer.write({row['question_id']: predicted_answer})

        print(f"Saved results to {save_path}")

    def _get_previous_keys(self) -> List[str]:
        """Get list of previously processed question IDs."""
        if 'prev_file' not in self.experiment_config:
            return []

        print('CONTINUE FROM PREVIOUS FILE')
        from ..utils.file_operations import load_jsonl

        prev_file = self.experiment_config['prev_file']
        list_jsonl = load_jsonl(prev_file)
        return [list(value.keys())[0] for value in list_jsonl]

    def _setup_question_folder(self, question_id: str) -> None:
        """Setup folder for current question."""
        self.experiment_config['cur_ques'] = question_id
        save_config(self.experiment_config_dir, self.experiment_config)

        # Create question folder
        path = os.path.join(self.experiment_folder, question_id)
        ques_folder = create_folder(path)
        init_ques_folder(ques_folder)

    def _get_description(self, row: pd.Series) -> str:
        """Get description if included in experiment configuration."""
        if (self.experiment_config['agent'] is not None and
            'description' in self.experiment_config['agent']):
            print('DESCRIPTION INCLUDED!')
            return row['description']
        return ''

    def _process_with_agents(self, prompt: str, row: pd.Series,
                           meta_agents: Union[List, Any]) -> str:
        """Process prompt with meta agents."""
        if isinstance(meta_agents, list):
            try:
                if 'reasoning' in self.experiment_config['agent']:
                    return self.reasoning_agent.loop(
                        prompt=prompt,
                        question=row['question_text'],
                        meta_agents=meta_agents
                    )
                elif 'qafirst' in self.experiment_config['agent']:
                    return self.reasoning_agent.loop_no_reasoning(
                        prompt=prompt,
                        meta_agents=meta_agents
                    )
                else:
                    prompt_3 = 'Also, your answer must include detail evidences!'
                    return meta_agents[0].run(prompt + prompt_3)
            except Exception as e:
                print(f"Error processing with agents: {e}")
                # Fallback processing
                return self._fallback_processing(prompt, row, meta_agents)
            finally:
                self._save_observation(meta_agents[0])
        else:
            return meta_agents(
                messages=[{'content': prompt, 'role': 'user'}]
            ).content

    def _fallback_processing(self, prompt: str, row: pd.Series,
                           meta_agents: List) -> str:
        """Fallback processing when main processing fails."""
        if 'reasoning' in self.experiment_config['agent']:
            return self.reasoning_agent.loop(
                prompt=prompt,
                question=row['question_text'],
                meta_agents=meta_agents
            )
        elif 'qafirst' in self.experiment_config['agent']:
            return self.reasoning_agent.loop_no_reasoning(
                prompt=prompt,
                meta_agents=meta_agents
            )
        else:
            prompt_3 = 'Also, your answer must include detail evidences!'
            return meta_agents[0].run(prompt + prompt_3)

    def _save_observation(self, meta_agent: Any) -> None:
        """Save agent observation to file."""
        dir_log = os.path.abspath(os.path.join(
            "log", self.experiment_name, str(self.experiment_config['part'])
        ))
        out = {"observation": str(meta_agent.memory.steps)}
        file_path = os.path.join(
            dir_log, self.experiment_config['cur_ques'], 'observation.jsonl'
        )
        write_json(out, file_path)