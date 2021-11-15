"""
Snake, but multiplayer
Created by sheepy0125
14/11/2021

Common (shared) code!
"""

### Global imports ###
import hisock
from tools import Logger
from os import environ
from pathlib import Path

### Credits ###
if not environ["multiplayer_snake_credits_shown"]:
    import constants

    Logger.log(f"Using hisock {hisock.constants.__version__}")
    Logger.log(
        f"Version {constants.__version__} of {constants.__name__} "
        f"created by {constants.__author__} "
        f"(copyright {constants.__copyright__} "
        f"under the {constants.__license__} license)"
    )
    environ["multiplayer_snake_credits_shown"] = "probably yeah sure"

    del constants
del environ

### Constants ###
ROOT_PATH: Path = Path(__file__).parent.parent
DEFAULT_CONFIG_PATH: Path = ROOT_PATH / "config.jsonc"
