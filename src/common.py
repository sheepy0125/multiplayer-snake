"""
Snake, but multiplayer
Created by sheepy0125
14/11/2021

Common (shared) code!
"""

### Setup ###
# Global imports
import hisock
import pygame
from pathlib import Path

# Other imports (must be deleted later)
from os import environ
import constants
from tools import Logger

### Credits ###
if not "multiplayer_snake_credits" in environ:
    Logger.log(f"Using hisock {hisock.constants.__version__}")
    Logger.log(
        f"Version {constants.__version__} of {constants.__name__} "
        f"created by {constants.__author__} "
        f"(copyright {constants.__copyright__} "
        f"under the {constants.__license__} license)"
    )
    environ["multiplayer_snake_credits"] = "probably yeah sure"

### Constants ###
ROOT_PATH: Path = Path(__file__).parent.parent
DEFAULT_CONFIG_PATH: Path = ROOT_PATH / "config.jsonc"

### Delete other imports ###
del environ, constants, Logger
