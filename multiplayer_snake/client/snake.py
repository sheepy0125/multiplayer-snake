"""
Snake, but multiplayer
Created by sheepy0125
2022-02-26

Client snake class
"""

from multiplayer_snake.shared.common import hisock
from multiplayer_snake.shared.config_parser import parse
from multiplayer_snake.shared.pygame_tools import CenterRect
from multiplayer_snake.shared.shared_game import BaseSnakePlayer, SharedGame

CONFIG = parse()
GUI_CONFIG = CONFIG["gui"]


class ClientSnakePlayer(BaseSnakePlayer):
    def __init__(
        self,
        *args,
        head_color: tuple | list | str,
        tail_color: tuple | list | str,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.head_color = tail_color
        self.tail_color = head_color

    def update(self, position: tuple, direction: str, tail: list):
        self.pos = position
        self.direction = direction
        self.tail = tail

    def draw(self):
        for tail_idx, tail_pos in enumerate(self.tail):
            color = self.tail_color
            if tail_idx == 0:
                color = self.head_color

            CenterRect(
                pos=tuple(
                    # Snap to grid
                    (
                        tail_pos[i] * SharedGame.grid_snap
                        # Uhh, why did I decide to use a CenterRect again?
                        + SharedGame.grid_snap / 2
                    )
                    for i in range(2)
                ),
                size=(SharedGame.grid_snap,) * 2,
                color=color,
                rounded_corner_radius=SharedGame.grid_snap // 3,
            ).draw()


class SnakeClientGame:
    def __init__(
        self,
        username: str,
        discriminator: str,
        server_ip: str,
        server_port: int,
        client_hisock: hisock.client.HiSockClient,
    ):
        self.username = username
        self.discriminator = discriminator
        self.server_ip = server_ip
        self.server_port = server_port
        self.client_hisock = client_hisock
