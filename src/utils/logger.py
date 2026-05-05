from loguru import logger
import sys
import os

def setup_logger(config):
    log_level = config.get("logging", {}).get("level", "INFO")
    log_file = config.get("logging", {}).get("file", "./logs/search_engine.log")
    rotation = config.get("logging", {}).get("rotation", "1 week")
    retention = config.get("logging", {}).get("retention", "1 month")
    
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    logger.remove()
    
    logger.add(
        sys.stdout,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level=log_level
    )
    
    logger.add(
        log_file,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level=log_level,
        rotation=rotation,
        retention=retention
    )
    
    return logger