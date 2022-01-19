__version__ = "0.3.6"

import logging
import sys

from .activity import Activities, Activity
from .client import GarminClient
from .download import ActivitiesDownloader
from .wellness import Wellness

# Create logger
logger = logging.getLogger(__name__)

# Avoid duplicate handlers
logger.handlers = []

# Create STDERR handler
handler = logging.StreamHandler(sys.stderr)
handler.setFormatter(
    logging.Formatter("%(asctime)s %(levelname)s - %(message)s", "%Y-%m-%d %H:%M:%S")
)
handler.setLevel(logging.INFO)
logger.addHandler(handler)

# Prevent multiple logging if called from other packages
logger.propagate = False
logger.setLevel(logging.INFO)
