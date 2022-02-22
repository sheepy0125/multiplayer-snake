"""
Snake, but multiplayer
Created by sheepy0125
2021-11-14

Server side code!
"""

### Setup ###
import constants
from multiplayer_snake.shared.common import hisock, pygame, Path
from multiplayer_snake.shared.tools import (
    Logger,
    get_public_ip,
    get_discriminator,
    check_username,
)
from multiplayer_snake.shared.pygame_tools import (
    GlobalPygame,
    Text,
    Button,
    CenterRect,
    Widget,
)
from multiplayer_snake.shared.config_parser import parse
from multiplayer_snake.shared.shared_game import BaseSnakePlayer
from time import time
from datetime import timedelta

CONFIG: dict = parse()
GUI_CONFIG: dict = CONFIG["gui"]
SERVER_CONFIG = CONFIG["server"]

# Setup pygame
pygame.init()
GlobalPygame.window = pygame.display.set_mode(GUI_CONFIG["window_size"])
pygame.display.set_caption(f"{constants.__name__} Server (GUI)")

# Setup hisock
server = hisock.server.ThreadedHiSockServer(
    (hisock.utils.get_local_ip(), CONFIG["server"]["port"]),
    max_connections=2,
)

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

        # Update players
        for player in self.players_online:
            player.update()

    def add_player(self, ip_address: str, username: str) -> bool:
        """Adds a player to the game, returns if valid"""

        # Too many players already
        if len(self.players_online) >= self.num_players:
            return False

        # Username isn't good
        if not check_username(username):
            return False

        # Everything seems fine, add the player
        self.players_online.append(
            ServerSnakePlayer(
                default_pos=(0, 0),
                default_length=1,
                identifier=f"{username}#{get_discriminator()}",
                ip_address=ip_address,
            )
        )


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


### Server handlers ###
@server.on("join")
def on_client_join(client_data):
    Logger.log(
        f"{client_data.name} ({hisock.iptup_to_str(client_data.ip)})"
        " connected to the server"
    )

    if not snake_game.add_player(client_data.ip, client_data.name):
        # Failed to join, disconnect player
        server.disconnect_client(client_data)


@server.on("connect_to_game")
def on_client_connect_to_game(client_data: dict, username: str):
    success = snake_game.add_player(ip=client_data["ip"], username=username)

    if success:
        Logger.log(
            f"Client with IP {hisock.iptup_to_str(client_data['ip'])} connected to the"
            f" server with username {username}."
        )

    server.send_client(
        client_data["ip"], "connect_to_game_response", {"success": success}
    )


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
        GlobalPygame.window.fill(GUI_CONFIG["colors"]["background"])

        # Draw widgets
        for widget in self.widgets:
            widget.draw()


### Widgets ###
class ServerWidget(Widget):
    def __init__(self, *args, **kwargs):
        # Colors and stuff
        text_size = GUI_CONFIG["text_size"]
        text_color = GUI_CONFIG["colors"]["widget"]["text"]
        padding = GUI_CONFIG["widget_padding"]
        widget_color = GUI_CONFIG["colors"]["widget"]["background"]
        border_color = GUI_CONFIG["colors"]["widget"]["border"]

        super().__init__(
            text_size=text_size,
            text_color=text_color,
            padding=padding,
            widget_color=widget_color,
            border_color=border_color,
            *args,
            **kwargs,
        )

        if CONFIG["verbose"]:
            Logger.log(f"Created {self.identifier} widget")


class PlayersListWidget(ServerWidget):
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
            len(self.text_widgets["mutable"]) == len(snake_game.players_online) * 2
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
                    str(player.identifier),
                    offset=(num * 2 + 2),  # 2 because of the title
                )
            )
            mutable_text_widgets.append(
                self.create_text(
                    hisock.utils.iptup_to_str(player.ip_address),
                    offset=(num * 2 + 2 + 1),  # 2 because of the title
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


class ServerStatusWidget(ServerWidget):
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
server.start()
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
