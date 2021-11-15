"""
Snake, but multiplayer
Created by sheepy0125
14/11/2021

Config parser!
"""

### Setup ###
from jsonc_parser.parser import JsoncParser
from jsonc_parser.errors import FileError, ParserError
from common import DEFAULT_CONFIG_PATH, Path
from tools import Logger

### Parse ###
def parse(config_path: Path | str | None = None) -> dict:
    """
    Parse config, return a dictionary
    If config_path is None, use default config path
    """

    if config_path is None:
        config_path = DEFAULT_CONFIG_PATH

    try:
        with open(config_path, "r") as config_file:
            config: dict = dict(JsoncParser.parse_str(config_file.read()))
    except FileNotFoundError:
        Logger.fatal(f"Config filepath ({config_path!s}) doesn't exist")
    except ParserError:
        Logger.fatal(f"Config file isn't a valid JSONC file")
    else:
        Logger.log(
            f"Loaded {len(config['server'].keys())} keys for server config and "
            f"{len(config['client'].keys())} keys for client config"
        )
        return config

    # The JSON file being invalid, cannot continue
    Logger.fatal("Couldn't load config file (UNRECOVERABLE)")
    exit(1)
