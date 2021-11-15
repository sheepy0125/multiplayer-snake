"""
Snake, but multiplayer
Created by sheepy0125
14/11/2021

Server side code!
"""

### Setup ###
from common import hisock, Path
from config_parser import parse

### Parse config ###
config: dict = parse()
