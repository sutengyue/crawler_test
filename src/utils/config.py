import yaml
import os

def load_config(config_path: str = "./config.yaml") -> dict:
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    
    return config

def get_config_value(config: dict, key: str, default=None):
    keys = key.split(".")
    value = config
    for k in keys:
        value = value.get(k, default)
        if value is None:
            return default
    return value