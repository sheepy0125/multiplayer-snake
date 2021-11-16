"""
Snake, but multiplayer
Created by sheepy0125
14/11/2021

Server side code!
"""

# TODO: make a class that will take care of things like players online and all
# TODO: the positions of the snek and food
# TODO: Priority: high (will def. need when implementing the actual game)


### Setup ###
import constants
from common import hisock, pygame, Path
from tools import Logger
from pygame_tools import GlobalWindow, Text, Button, CenterRect
from config_parser import parse

CONFIG: dict = parse()
GUI_CONFIG: dict = CONFIG["gui"]
SERVER_CONFIG = CONFIG["server"]
# TODO: add config checker

# Setup pygame
pygame.init()
GlobalWindow.window = pygame.display.set_mode(GUI_CONFIG["window_size"])
pygame.display.set_caption(f"{constants.__name__} Server (GUI)")

### Classes ###
class ServerWindow:
    """Handles all the widgets inside the window"""

    def __init__(self):
        """No params as this will use CONFIG"""

        self.widgets = self.create_widgets()

        if SERVER_CONFIG["verbose"]:
            Logger.log("Server window created")

    def create_widgets(self) -> list:
        if SERVER_CONFIG["verbose"]:
            Logger.log("Created widgets")

        widgets: list = []

        widgets.append(PlayersListWidget())

        return widgets

    def draw(self):
        """Draws all the widgets and the main window"""

        # Draw background
        GlobalWindow.window.fill(GUI_CONFIG["colors"]["background"])

        # Draw widgets
        for widget in self.widgets:
            widget.draw()


### Widgets ###
class Widget:
    """Base widget class"""

    def __init__(
        self,
        pos: tuple,
        size: tuple,
        identifier: str | int = "unknown widget",
    ):
        self.pos = pos
        self.size = size
        self.identifier = identifier

        self.rect = pygame.Rect(self.pos, self.size)

        if SERVER_CONFIG["verbose"]:
            Logger.log(f"Created widget {self.identifier}")

    def draw(self):
        # Main widget
        pygame.draw.rect(
            GlobalWindow.window,
            GUI_CONFIG["colors"]["widget"]["background"],
            self.rect,
            border_radius=10,
        )
        # Widget border
        pygame.draw.rect(
            GlobalWindow.window,
            GUI_CONFIG["colors"]["widget"]["border"],
            self.rect,
            border_radius=10,
            width=2,
        )


class PlayersListWidget(Widget):
    def __init__(self):
        super().__init__(
            pos=(GUI_CONFIG["widget_padding"], GUI_CONFIG["widget_padding"]),
            size=(
                GUI_CONFIG["window_size"][0] // 4 * 1,
                GUI_CONFIG["window_size"][1] - (GUI_CONFIG["widget_padding"] * 2),
            ),
        )

        self.text_widgets: list[Text] = []

        # When the widget is created, no players will be online
        # If this is not the case, then oh well!
        # self.update([])
        # Testing!
        self.update(["Player 1", "Player 2"])

    def update(self, players_online: list):
        for num, player in enumerate(players_online):
            if SERVER_CONFIG["verbose"]:
                Logger.log(f"Created text widget for player {player}")

            self.text_widgets.append(
                Text(
                    player,
                    pos=(
                        self.pos[0] + self.size[0] // 2,
                        (
                            self.pos[1]
                            + ((GUI_CONFIG["text_size"] + 4) * num + 1)
                            + GUI_CONFIG["widget_padding"]
                        ),
                    ),
                    size=GUI_CONFIG["text_size"],
                    color=GUI_CONFIG["colors"]["widget"]["text"],
                )
            )

    def draw(self):
        super().draw()

        for text in self.text_widgets:
            text.draw()


### Main ###
server_win = ServerWindow()
while True:
    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit(0)  # TODO: add proper exit

    # Draw
    server_win.draw()
    pygame.display.flip()
