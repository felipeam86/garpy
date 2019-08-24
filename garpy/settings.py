# -*- coding: utf-8 -*-

import collections
import logging
import sys
import yaml
from pathlib import Path

from pythonjsonlogger import jsonlogger

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


def get_logger(name,
               filename=config.get('log_filepath'),
               streamhandler=config.get('log_stream', True)):

    # Create logger
    logger = logging.getLogger(name)

    # Avoid duplicate handlers
    logger.handlers = []

    if streamhandler:
        formatter = logging.Formatter(
            '%(asctime)s-%(name)s-%(levelname)s - %(message)s',
            '%Y-%m-%d-%H:%M:%S'
        )
        # Create STDERR handler
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(formatter)
        handler.setLevel(logging.DEBUG)
        logger.addHandler(handler)

    if filename is not None:
        # Create formatter and add it to the handler
        formatter = jsonlogger.JsonFormatter(
            "%(asctime) %(name) %(levelname) %(message)",
        )
        # Create json formatter
        filehandler = logging.FileHandler(filename)
        filehandler.setFormatter(formatter)
        filehandler.setLevel(logging.DEBUG)
        logger.addHandler(filehandler)

    # Prevent multiple logging if called from other packages
    logger.propagate = False
    logger.setLevel(logging.DEBUG)

    return logger


logger = get_logger(__name__)

if len(config_files) > 0:
    logger.info(f"Loaded configuration from the following file(s): {config_files}")

# Format and typing of the config goes here, e.g.:
# config['root_path'] = Path(config['root_path']).expanduser()

# Format and typing of the config goes here, e.g.:
config['backup-dir'] = Path('.').absolute() / config['backup-dir']
