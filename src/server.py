"""
Snake, but multiplayer
Created by sheepy0125
14/11/2021

Server side code!
"""

### Setup ###
import constants
from common import hisock, pygame, Path
from tools import Logger
from pygame_tools import GlobalWindow, Text, Button, CenterRect
from config_parser import parse

CONFIG: dict = parse()["server"]
# TODO: add config checker

# Setup pygame
pygame.init()
GlobalWindow.window = pygame.display.set_mode(CONFIG["window_size"])
pygame.display.set_caption(f"{constants.__name__} Server (GUI)")

### Classes ###
class ServerWindow:
    """Handles all the widgets inside the window"""

    def __init__(self):
        """No params as this will use CONFIG"""

        # Hardcoded variables for fun!
        self.background_color: tuple = (211, 211, 211)  # Light gray
        self.text_color: tuple = (0, 0, 0)  # Black

        self.widgets = self.create_widgets()

        if CONFIG["verbose"]:
            Logger.log("Server window created")

    def create_widgets(self) -> list:
        if CONFIG["verbose"]:
            Logger.log("Created widgets")

        return []

    def draw(self):
        """Draws all the widgets and the main window"""

        # Draw background
        GlobalWindow.window.fill(self.background_color)

        # Draw widgets
        for widget in self.widgets:
            widget.draw()
