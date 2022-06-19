"""
Snake, but multiplayer
Created by sheepy0125
2022-02-26

Client food class
"""

### Setup ###
from multiplayer_snake.shared.pygame_tools import CenterRect
from multiplayer_snake.shared.shared_game import SharedGame
from multiplayer_snake.shared.config_parser import parse

CONFIG = parse()


class ClientFood:
    def __init__(self, pos: tuple):
        self.pos = pos
        self.color = CONFIG["gui"]["colors"]["food"]

    def draw(self):
        CenterRect(
            pos=self.pos,
            size=(SharedGame.grid_snap, SharedGame.grid_snap),
            color=CONFIG["gui"]["colors"]["food"],
        ).draw()
