# -*- coding: utf-8 -*-

import collections
import logging
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)

PACKAGE_NAME = 'garpy'


def recursive_update(d, u):
    for k, v in u.items():
        if isinstance(v, collections.Mapping):
            d[k] = recursive_update(d.get(k, {}), v)
        else:
            d[k] = v
    return d


def load_config_file(path: Path):
    if path.exists():
        return yaml.load(path.read_text(), Loader=yaml.FullLoader)\
                   .get(PACKAGE_NAME, {})
    else:
        return {}


default_config = Path(__file__).parent / 'resources' / 'default_config.yaml'
config = load_config_file(default_config)

extra_config_files = [
    Path('/etc/garpy/config.yaml'),
    Path('~/.config/garpy/config.yaml').expanduser(),
    Path('config.yaml'),
]

config_files = []
for config_file in extra_config_files:
    extra_config = load_config_file(config_file)
    if extra_config:
        recursive_update(config, extra_config)
        config_files.append(config_file)


if len(config_files) > 0:
    logger.debug(f"Loaded configuration from the following file(s): {config_files}")


class Password:
    def __init__(self, password: str) -> None:
        self.password = password or ''

    def __repr__(self) -> str:
        return '*' * len(self.password)

    def get(self) -> str:
        return self.password

    def __bool__(self):
        return bool(self.password)


# Format and typing of the config goes here, e.g.:
config['backup-dir'] = Path('.').absolute() / config['backup-dir']
if config.get('password') is not None:
    config['password'] = Password(config.get('password'))
