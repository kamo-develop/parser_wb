import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

from loguru import logger

ROOT_DIR = Path(__file__).resolve().parent

@dataclass
class Config:
    proxies: List[Dict[str, str]]
    query: str
    count_pages: int
    count_workers: int
    count_max_scroll: int
    random_pause_range: Tuple[float, float]
    output_path: str


def load_config() -> Config:
    try:
        with open(ROOT_DIR / "config.json", "r", encoding="utf-8") as f:
            config_json = json.load(f)
            if "random_pause_range" in config_json:
                config_json["random_pause_range"] = tuple(config_json["random_pause_range"])

            return Config(**config_json)
    except Exception as e:
        logger.exception("Config file reading error")


conf: Config = load_config()
