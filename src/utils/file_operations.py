"""File operation utilities."""

import json
import jsonlines
import os
from typing import List, Dict, Any


def load_jsonl(filename: str) -> List[Dict[str, Any]]:
    """Load data from JSONL file.

    Args:
        filename: Path to JSONL file

    Returns:
        List of dictionaries from the JSONL file
    """
    with open(filename, 'r', encoding='utf-8') as file:
        return [json.loads(line) for line in file]


def create_folder(path: str) -> str:
    """Create folder if it doesn't exist.

    Args:
        path: Path to create

    Returns:
        The created path
    """
    os.makedirs(path, exist_ok=True)
    return path


def init_ques_folder(path: str) -> None:
    """Initialize question folder with required files.

    Args:
        path: Path to question folder
    """
    files = [
        'web.jsonl',
        'qa.jsonl',
        'product_qa.jsonl',
        'product_sql.jsonl',
        'att.jsonl',
        'observation.jsonl',
        'tavily.jsonl'
    ]
    for file in files:
        file_dir = os.path.join(path, file)
        with open(file_dir, 'w', encoding='utf-8'):
            pass


def write_json(data: Dict[str, Any], path: str) -> None:
    """Write JSON data to file.

    Args:
        data: Data to write
        path: Path to write to
    """
    with open(path, "a", encoding="utf-8") as file:
        file.write(json.dumps(data, ensure_ascii=False) + "\n")