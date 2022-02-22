"""
Snake, but multiplayer
Created by sheepy0125
2021-11-14

Common (shared) code!
"""

### Setup ###
# Global imports
import hisock
import pygame
import pygame_gui
from pathlib import Path
from multiplayer_snake.shared.tools import Logger

# Other imports (must be deleted later)
import multiplayer_snake.constants as constants
from os import environ

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
del environ, constants
