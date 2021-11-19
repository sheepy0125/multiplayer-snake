"""
Snake, but multiplayer
Created by sheepy0125
14/11/2021

Server side code!
"""

### Setup ###
import constants
from common import hisock, pygame, Path
from tools import Logger, get_public_ip
from pygame_tools import GlobalWindow, Text, Button, CenterRect
from config_parser import parse
from shared_game import BaseSnakePlayer
from time import time
from datetime import timedelta

CONFIG: dict = parse()
GUI_CONFIG: dict = CONFIG["gui"]
SERVER_CONFIG = CONFIG["server"]

# Setup pygame
pygame.init()
GlobalWindow.window = pygame.display.set_mode(GUI_CONFIG["window_size"])
pygame.display.set_caption(f"{constants.__name__} Server (GUI)")

### Classes ###
class SnakeGame:
    """Handles everything that will be sent to the clients"""

    def __init__(self, num_players: int = 2):
        """Please note, `num_players` currently does nothing"""

        self.num_players = 2
        self.players_online: list[BaseSnakePlayer] = []
        self.round: int = 0  # Will be set to 1 when the game is started
        self.uptime: int = 0  # Will only be integers (not ms)
        self.start_time: int = 0  # This'll be the UNIX timestamp when the game started
        self.uptime_changed: bool = False  # LOL

    def update(self):
        """Updates the game (must be started first)"""

        self.uptime = int(time() - self.start_time)


snake_game = SnakeGame()


class ServerSnakePlayer(BaseSnakePlayer):
    """Server side snake player"""

    def _reset(self, ip_address: str, *args, **kwargs):
        """BaseSnakePlayer reset, but it has more (oh no)"""

        self.ip_address = ip_address
        super()._reset(*args, **kwargs)

    def snake_died(self, reason: str = "unknown"):
        super().snake_died(reason)
        snake_game.snake_died(identifier=self.identifier, reason=reason)


class ServerWindow:
    """Handles all the widgets inside the window"""

    def __init__(self):
        """No params as this will use CONFIG"""

        self.widgets = self.create_widgets()

        if CONFIG["verbose"]:
            Logger.log("Server window created")

    def create_widgets(self) -> list:
        if CONFIG["verbose"]:
            Logger.log("Created widgets")

        widgets: list = [PlayersListWidget(), ServerStatusWidget()]

        return widgets

    def update(self):
        """Updates all the widgets"""

        for widget in self.widgets:
            widget.update()

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

        if CONFIG["verbose"]:
            Logger.log(f"Created widget {self.identifier}")

    def create_text(
        self,
        text: str,
        offset: int,
        size: int = GUI_CONFIG["text_size"],
        color: tuple = GUI_CONFIG["colors"]["text"],
    ):
        return Text(
            text,
            pos=(
                self.pos[0] + self.size[0] // 2,
                self.pos[1]
                + (offset * GUI_CONFIG["text_size"])
                + GUI_CONFIG["widget_padding"],
            ),
            size=size,
            color=color,
        )

    def update(self):
        # Will be overwritten hopefully
        Logger.warn(f"Widget {self.identifier} has no update method")

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
    """Widget for players online"""

    def __init__(self):
        super().__init__(
            pos=(GUI_CONFIG["widget_padding"], GUI_CONFIG["widget_padding"]),
            size=(
                GUI_CONFIG["window_size"][0] // 4 * 1,
                GUI_CONFIG["window_size"][1] // 2 - (GUI_CONFIG["widget_padding"] * 2),
            ),
            identifier="players list",
        )

        self.text_widgets: dict = {
            "immutable": [
                self.create_text("Players online", offset=0),
            ],
            "mutable": [],
        }
        self.update(do_check=False)

    def update(self, do_check: bool = True):
        if do_check and (
            len(self.text_widgets["mutable"]) == len(snake_game.players_online)
        ):
            return

        if CONFIG["verbose"]:
            Logger.log(
                f"Updating players (players online: {len(snake_game.players_online)})"
            )

        mutable_text_widgets: list[Text] = []
        for num, player in enumerate(snake_game.players_online):
            mutable_text_widgets.append(
                self.create_text(
                    f"{player.identifier} ({player.ip_address})",
                    offset=(num + 2),  # 2 because of the title
                ),
            )

            if CONFIG["verbose"]:
                Logger.log(f"Created text widget for player snake {player.identifier}")

            self.text_widgets["mutable"] = mutable_text_widgets

    def draw(self):
        super().draw()

        for text_list in self.text_widgets.values():
            for text in text_list:
                text.draw()


class ServerStatusWidget(Widget):
    """Widget for telling stats about the server"""

    def __init__(self):
        super().__init__(
            pos=(GUI_CONFIG["widget_padding"], GUI_CONFIG["window_size"][1] // 2),
            size=(
                GUI_CONFIG["window_size"][0] // 4 * 1,
                GUI_CONFIG["window_size"][1] // 2 - (GUI_CONFIG["widget_padding"] * 2),
            ),
            identifier="server status",
        )

        self.text_widgets: dict = {
            "immutable": [
                self.create_text("Server status", offset=0),
                self.create_text(
                    f"Server local IP: {hisock.utils.get_local_ip()}", offset=2
                ),
                self.create_text(f"Server public IP: {get_public_ip()}", offset=3),
                self.create_text(f"Server port: {CONFIG['server']['port']}", offset=4),
            ],
            "mutable": [None],
        }
        self.update(do_check=False)

    def update(self, do_check: bool = True):
        if (not do_check) or snake_game.uptime_changed:
            uptime_text_widget = self.create_text(
                f"Uptime: {str(timedelta(snake_game.uptime))!s}", offset=5
            )
            self.text_widgets["mutable"] = [uptime_text_widget]
            if CONFIG["verbose"]:
                Logger.log(f"Created text widget for server uptime")

            self.text_widgets["mutable"][0] = uptime_text_widget

    def draw(self):
        super().draw()

        for text_list in self.text_widgets.values():
            for text in text_list:
                text.draw()


### Main ###
server_win = ServerWindow()
while True:
    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit(0)  # TODO: add proper exit

        if event.type == pygame.KEYDOWN:
            # Debug!!!
            if event.key == pygame.K_SPACE:
                snake_game.players_online.append(
                    ServerSnakePlayer(
                        default_pos=(0, 0),
                        default_length=1,
                        identifier="Testing!",
                        ip_address="192.168.86.60",
                    )
                )

            elif event.key == pygame.K_r:
                for player in snake_game.players_online:
                    player.reset()

    # Update
    server_win.update()

    # Draw
    server_win.draw()
    pygame.display.flip()
