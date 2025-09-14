"""Configuration management utilities."""

import json
import os
import yaml
from typing import Dict, Any, Tuple


def load_config(yaml_path: str) -> Dict[str, Any]:
    """Load configuration from YAML file.

    Args:
        yaml_path: Path to the YAML configuration file

    Returns:
        Dictionary containing configuration data
    """
    with open(yaml_path, "r", encoding="utf-8") as stream:
        try:
            return yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(f"Error loading config from {yaml_path}: {exc}")
            return {}


def load_experiment_config(config_dir: str = "config/experiment.yaml") -> Tuple[str, Dict[str, Any]]:
    """Load experiment configuration.

    Args:
        config_dir: Path to experiment config file

    Returns:
        Tuple of (config_directory_path, config_data)
    """
    experiment_config_dir = load_config(config_dir)['dir']
    experiment_config = load_config(experiment_config_dir)
    return experiment_config_dir, experiment_config


def save_config(yaml_path: str, yaml_data: Dict[str, Any]) -> None:
    """Save configuration to YAML file.

    Args:
        yaml_path: Path to save the YAML file
        yaml_data: Configuration data to save
    """
    yaml_file = yaml.dump(yaml_data, default_flow_style=False)
    with open(yaml_path, "w", encoding="utf-8") as file:
        file.write(yaml_file)