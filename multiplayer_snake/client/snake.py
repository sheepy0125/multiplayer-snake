from multiplayer_snake.shared.common import hisock, pygame
from multiplayer_snake.shared.config_parser import parse
from multiplayer_snake.shared.pygame_tools import CenterRect
from multiplayer_snake.shared.shared_game import BaseSnakePlayer, SharedGame

CONFIG = parse()
GUI_CONFIG = CONFIG["gui"]


class ClientSnakePlayer(BaseSnakePlayer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tail_color = GUI_CONFIG["colors"]["snek_one_tail"]
        self.head_color = GUI_CONFIG["colors"]["snek_one_head"]

    def draw(self):
        for tail_idx, tail_pos in enumerate(self.tail):
            color = self.tail_color
            if tail_idx == 0:
                color = self.head_color

            CenterRect(
                tail_pos, (SharedGame.grid_snap,) * 2, color, SharedGame.grid_snap // 5
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
