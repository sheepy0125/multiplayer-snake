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
from shared_game import BaseSnakePlayer

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

        widgets: list = []
        widgets.append(PlayersListWidget())

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
        )

        self.text_widgets: dict = {
            "immutable": [
                Text(
                    "Players online",
                    pos=(
                        self.pos[0] + self.size[0] // 2,
                        self.pos[1] + GUI_CONFIG["widget_padding"],
                    ),
                    size=GUI_CONFIG["text_size"],
                    color=GUI_CONFIG["colors"]["widget"]["text"],
                )
            ],
            "mutable": [],
        }
        self.update(do_check=False)

    def update(self, do_check: bool = True):
        # Check if it changed at all (don't regen if not needed)
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
                Text(
                    f"{player.identifier} ({player.ip_address})",
                    pos=(
                        self.pos[0] + self.size[0] // 2,
                        (
                            self.pos[1]
                            + ((GUI_CONFIG["text_size"] + 4) * (num + 2))  # 2 b/c title
                            + GUI_CONFIG["widget_padding"]
                        ),
                    ),
                    size=GUI_CONFIG["text_size"],
                    color=GUI_CONFIG["colors"]["widget"]["text"],
                )
            )

            if CONFIG["verbose"]:
                Logger.log(f"Created text widget for player snake {player.identifier}")

            self.text_widgets["mutable"] = mutable_text_widgets

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
