# -*- coding: utf-8 -*-

import logging
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)


def recursive_update(original_dict: dict, new_dict: dict) -> dict:
    """Recursively update original_dict with new_dict"""
    for new_key, new_value in new_dict.items():
        if isinstance(new_value, dict):
            original_dict[new_key] = recursive_update(
                original_dict.get(new_key, {}), new_value
            )
        else:
            original_dict[new_key] = new_value
    return original_dict


class Password:
    def __init__(self, password: str) -> None:
        self.password = password or ""

    def __repr__(self) -> str:
        return "*" * len(self.password)

    def get(self) -> str:
        return self.password

    def __bool__(self):
        return bool(self.password)


# Configurations are loaded from the defaults of the package and eventually a local config.yaml file
config_files = [
    Path(__file__).parent / "resources" / "default_config.yaml",
    Path("config.yaml"),
]

config = {}
for config_file in config_files:
    if config_file.exists():
        new_config = yaml.safe_load(config_file.read_text())
        if isinstance(new_config, dict):
            config = recursive_update(config, new_config)


config["backup-dir"] = Path(config["backup-dir"]).absolute()
config["password"] = Password(config.get("password"))
