import logging
import sys
from pathlib import Path


PACKAGE_ROOT = Path(__file__).parent.parent.parent

logger = logging.getLogger("Logger")
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler(sys.stdout))



