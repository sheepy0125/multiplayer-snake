"""
Snake, but multiplayer
Created by sheepy0125
16/11/2021

Client game code
"""

### Setup ###
import pygame_gui
import constants
from common import hisock, pygame
from tools import Logger, get_public_ip, get_discriminator, check_username
from pygame_tools import GlobalPygame, Text, Button, CenterRect, Widget
from config_parser import parse
from shared_game import BaseSnakePlayer, SharedGame

CONFIG = parse()
GUI_CONFIG = CONFIG["gui"]
CLIENT_CONFIG = CONFIG["client"]

# Setup pygame
pygame.init()
GlobalPygame.window = pygame.display.set_mode(GUI_CONFIG["window_size"])
GlobalPygame.clock = pygame.time.Clock()
pygame.display.set_caption(f"{constants.__name__} Client (GUI)")

### Classes ###
class ClientSnakePlayer(BaseSnakePlayer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tail_color: list[int] = GUI_CONFIG["snek_tail"]
        self.head_color: list[int] = GUI_CONFIG["snek_head"]

    def draw(self):
        for tail_idx, tail_block in enumerate(self.tail):
            color = self.tail_color
            if tail_idx == 0:
                color = self.head_color

            pygame.draw.rect(
                GlobalPygame.window,
                color,
                width=SharedGame.grid_snap,
                height=SharedGame.grid_snap,
                center=tail_block,
            )


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


### Connection screen ###
class ClientLogin(Widget):
    def __init__(self):
        # Variables
        self.username = ""
        self.discriminator = ""
        self.server_ip = ""

        # Setup
        self.ui_manager = pygame_gui.UIManager(GUI_CONFIG["window_size"])

        self.time_delta = GlobalPygame.clock.tick(60) / 1000

        self.text_widgets: list[Text] = []

    def main_loop(self):
        self.ui_manager.update(self.time_delta)
        self.ui_manager.draw_ui(GlobalPygame.window)
        GlobalPygame.window.fill(GUI_CONFIG["colors"]["background"])

    def handle_event(self, event: pygame.event.EventType):
        self.ui_manager.process_events(event)


client_connector = ClientLogin()
is_connecting = True
while is_connecting:
    client_connector.main_loop()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            is_connecting = False

        client_connector.handle_event(event)

    pygame.display.flip()
