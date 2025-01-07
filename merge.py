import argparse
import os
import yaml
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Set
from enum import Enum

class MergeStrategy(Enum):
    FIRST_WINS = "first-wins"
    LAST_WINS = "last-wins"
    ERROR_ON_CONFLICT = "error-on-conflict"

@dataclass
class ValueSource:
    value: Any
    source_file: str
    line_number: int

class ConfigMerger:
    def __init__(self, strategy: MergeStrategy):
        self.strategy = strategy
        self.values: Dict[str, ValueSource] = {}
        self.secrets: Dict[str, str] = {}
        self.conflicts: List[str] = []

    def add_value(self, path: str, value: Any, source: ValueSource):
        if path in self.values:
            existing = self.values[path]
            if existing.value != value:
                conflict = f"Conflict at {path}: {existing.value} ({existing.source_file}) vs {value} ({source.source_file})"
                if self.strategy == MergeStrategy.ERROR_ON_CONFLICT:
                    raise ValueError(conflict)
                self.conflicts.append(conflict)
                if self.strategy == MergeStrategy.LAST_WINS:
                    self.values[path] = source
            # FIRST_WINS: keep existing value
        else:
            self.values[path] = source


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", nargs="+", required=True, help="Input files/directories")
    parser.add_argument("-o", "--output", required=True, help="Output file")
    parser.add_argument(
        "-m","--merge-strategy",
        choices=[s.value for s in MergeStrategy],
        default=MergeStrategy.FIRST_WINS.value,
        help="Strategy for handling conflicts"
    )
    return parser.parse_args()

def collect_input_files(paths: List[str]) -> Set[str]:
    files = set()
    for path in paths:
        path = path.strip()
        if os.path.isfile(path):
            files.add(path)
        elif os.path.isdir(path):
            for root, _, filenames in os.walk(path):
                for filename in filenames:
                    files.add(os.path.join(root, filename))
    return files

def is_secrets_file(filename: str) -> bool:
    with open(filename, "r") as f:
        first_line = f.readline()
        return ': ' in first_line and '${' not in first_line

def process_yaml(merger: ConfigMerger, yaml_content: str, filename: str):
    try:
        config = yaml.safe_load(yaml_content)
        if not isinstance(config, dict):
            raise ValueError(f"Invalid YAML structure in {filename}")
        return process_dict(config, "", filename, merger)
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in {filename}: {e}")

def process_dict(d: dict, path: str, filename: str, merger: ConfigMerger):
    result = {}
    for key, value in d.items():
        current_path = f"{path}.{key}" if path else key
        if isinstance(value, dict):
            result[key] = process_dict(value, current_path, filename, merger)
        elif isinstance(value, list):
            result[key] = process_list(value, current_path, filename, merger)
        else:
            source = ValueSource(value, filename, 0)  # TODO: Track line numbers
            merger.add_value(current_path, value, source)
            result[key] = value
    return result

def process_list(l: list, path: str, filename: str, merger: ConfigMerger):
    result = []
    for i, item in enumerate(l):
        if isinstance(item, dict):
            result.append(process_dict(item, f"{path}[{i}]", filename, merger))
        elif isinstance(item, list):
            result.append(process_list(item, f"{path}[{i}]", filename, merger))
        else:
            result.append(item)
    return result

def merge_dicts(d1: dict, d2: dict, path: str, filename: str, merger: ConfigMerger) -> dict:
    """Recursively merge two dictionaries, preserving nested structures"""
    result = d1.copy()
    
    for key, value in d2.items():
        current_path = f"{path}.{key}" if path else key
        
        if key in result:
            # If both are dicts, merge them recursively
            if isinstance(value, dict) and isinstance(result[key], dict):
                result[key] = merge_dicts(result[key], value, current_path, filename, merger)
            # If both are lists, append unique items
            elif isinstance(value, list) and isinstance(result[key], list):
                result[key].extend(x for x in value if x not in result[key])
            # Otherwise handle as conflict
            else:
                source = ValueSource(value, filename, 0)
                merger.add_value(current_path, value, source)
                if merger.values[current_path].source_file == filename:
                    result[key] = value
        else:
            # New key, just add it
            result[key] = value
            if not isinstance(value, (dict, list)):
                source = ValueSource(value, filename, 0)
                merger.add_value(current_path, value, source)
    
    return result

def process_yaml(merger: ConfigMerger, yaml_content: str, filename: str):
    try:
        config = yaml.safe_load(yaml_content)
        if not isinstance(config, dict):
            raise ValueError(f"Invalid YAML structure in {filename}")
        return config  # Return raw config for merging
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in {filename}: {e}")

def main():
    args = parse_args()
    logging.basicConfig(level=logging.INFO)
    
    files = collect_input_files(args.input[0].split(","))
    merger = ConfigMerger(MergeStrategy(args.merge_strategy))
    
    # Process secret files first
    secret_files = {f for f in files if is_secrets_file(f)}
    config_files = files - secret_files
    
    for secret_file in secret_files:
        with open(secret_file, 'r') as f:
            for line in f:
                if ': ' in line and '${' not in line:
                    key, value = [x.strip() for x in line.split(':', 1)]
                    merger.secrets[key] = value
    
    # Process config files
    merged_config = {}
    for config_file in config_files:
        with open(config_file, 'r') as f:
            content = f.read()
            # Replace variables
            for key, value in merger.secrets.items():
                content = content.replace(f"${{{key}}}", value)
            config = process_yaml(merger, content, config_file)
            if not merged_config:
                merged_config = config
            else:
                merged_config = merge_dicts(merged_config, config, "", config_file, merger)
    
    if merger.conflicts:
        for conflict in merger.conflicts:
            logging.warning(conflict)
    
    # Write output
    with open(args.output, 'w') as f:
        yaml.dump(merged_config, f, default_flow_style=False)

if __name__ == "__main__":
    main()