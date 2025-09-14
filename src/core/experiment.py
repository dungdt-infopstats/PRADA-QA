"""Core experiment functionality."""

import datetime
import os
import sys
from typing import List, Optional, Dict, Any

from utils.config import load_experiment_config, save_config
from utils.file_operations import create_folder


class ExperimentManager:
    """Manages experiment configuration and setup."""

    def __init__(self):
        self.config_dir: Optional[str] = None
        self.config: Optional[Dict[str, Any]] = None
        self.experiment_name: Optional[str] = None
        self.experiment_folder: Optional[str] = None

    def setup_experiment(self, model_name: str, experiment_type: str, part: int,
                        data_choice: str, step: Optional[str] = None) -> None:
        """Setup experiment configuration.

        Args:
            model_name: Name of the model to use
            experiment_type: Type of experiment
            part: Experiment part number
            data_choice: Data choice for the experiment
            step: Optional step parameter
        """
        # Load experiment configuration
        self.config_dir, self.config = load_experiment_config()

        # Create datetime for experiment folder
        date_time = f'_{datetime.datetime.now().strftime("%Y-%m-%d %H-%M-%S")}'
        self.config['datetime'] = date_time

        # Set experiment parameters
        self.config['model'] = model_name.replace('.', '-').replace(':', '-').replace('/', '-')
        self.config['name'] = experiment_type
        self.config['agent'] = experiment_type.split('-')
        self.config['part'] = part
        self.config['model-id'] = model_name
        self.config['data_choice'] = data_choice

        if step:
            self.config['step'] = step

        # Save updated configuration
        save_config(self.config_dir, self.config)

        # Create experiment folders
        self._create_experiment_folders()

    def _create_experiment_folders(self) -> None:
        """Create necessary experiment folders."""
        log_dir = "log"

        # Create experiment name
        self.experiment_name = (
            f"{self.config['name']}_{self.config['model']}{self.config['datetime']}"
        )

        # Create experiment folder
        self.experiment_folder = create_folder(
            os.path.join(log_dir, self.experiment_name, str(self.config['part']))
        )

        # Create data folder
        create_folder(
            f"data/{self.config['model']}/{self.config['name']}"
        )

    def get_experiment_config(self) -> Dict[str, Any]:
        """Get current experiment configuration."""
        return self.config or {}

    def get_experiment_name(self) -> str:
        """Get current experiment name."""
        return self.experiment_name or ""

    def get_experiment_folder(self) -> str:
        """Get current experiment folder path."""
        return self.experiment_folder or ""


def validate_arguments(args: List[str], expected_count: int) -> None:
    """Validate command line arguments.

    Args:
        args: List of command line arguments
        expected_count: Expected number of arguments

    Raises:
        SystemExit: If argument count is incorrect
    """
    if len(args) != expected_count:
        print(f"Usage: python script.py requires {expected_count-1} arguments")
        sys.exit(1)