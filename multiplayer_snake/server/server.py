"""
Snake, but multiplayer
Created by sheepy0125
2021-11-14

Server side code!
"""

### Setup ###
import multiplayer_snake.constants as constants
from multiplayer_snake.shared.common import hisock, pygame, Logger
from multiplayer_snake.shared.tools import (
    get_public_ip,
    get_discriminator,
    check_username,
)
from multiplayer_snake.shared.pygame_tools import (
    GlobalPygame,
    Text,
    WrappedText,
    Widget,
)
from multiplayer_snake.shared.config_parser import parse
from multiplayer_snake.shared.shared_game import BaseSnakePlayer, SharedGame
from time import time
from datetime import timedelta
from os import _exit as force_exit
from io import TextIOWrapper
import sys

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
class GameAlreadyRunningError(Exception):
    ...


class SnakeGame:
    """Handles everything that will be sent to the clients"""

    def __init__(self):
        self.num_players = 2
        self.players_online: list[ServerSnakePlayer] = []
        self.round: int = 0
        self.uptime: int = 0  # Seconds
        self.uptime_changed: bool = False  # For the GUI
        self.running = False
        self.start_time: int = 0  # Unix timestamp
        self.last_update_time: float = 0.0  # Unix timestamp
        self.time_next_tick: float = 0.0  # Milliseconds

        self.default_spots = [
            (0, round(((SharedGame.height / 2) - 1), ndigits=1)),
            (SharedGame.width - 1, round(((SharedGame.height / 2) - 1), ndigits=1)),
        ]

    def get_data(self) -> dict:
        """Get data for updating the clients"""

        # Get the data
        return {
            "players": [player.get_data() for player in self.players_online],
            "round": self.round,
            "uptime": self.uptime,
            "uptime_changed": self.uptime_changed,
        }

    def update(self):
        """Updates the game (must be started first)"""

        original_uptime = self.uptime
        self.uptime = int(time() - self.start_time)
        self.uptime_changed = original_uptime == self.uptime

        # Is it time for the next tick?
        time_next_tick = SERVER_CONFIG["time_until_update"] - (
            time() - self.last_update_time
        )
        self.time_next_tick = time_next_tick
        if time_next_tick > 0:
            return

        print("next tick", time_next_tick, self.last_update_time)
        self.last_update_time += SERVER_CONFIG["time_until_update"]

        # Update players
        for player in self.players_online:
            player.update()

        # Update clients
        update_clients_with_data()

    def run(self):
        """Run everything. Should be called every frame"""

        if not self.running:
            return

        self.update()

    def start(self):
        """Start the game"""

        if self.running:
            raise GameAlreadyRunningError

        self.running = True
        self.start_time = int(time())
        self.last_update_time = time()

        # Alert everyone that the game has started
        server.send_all_clients("game_started")

    def add_player(self, ip_address: str, username: str) -> bool:
        """Adds a player to the game, returns if valid"""

        # Too many players already
        if len(self.players_online) >= self.num_players:
            return False

        # Username isn't good
        if not check_username(username):
            return False

        # Everything seems fine, add the player

        # Get the default position
        default_pos = self.default_spots[len(self.players_online)]

        self.players_online.append(
            ServerSnakePlayer(
                default_pos=default_pos,
                default_length=1,
                identifier=f"{username}#{get_discriminator()}",
                ip_address=ip_address,
            )
        )

    def snake_died(self, snake_identifier: str):
        # Game over
        server.send_all_clients("game_over", f"{snake_identifier} died")


snake_game = SnakeGame()


class ServerSnakePlayer(BaseSnakePlayer):
    """Server side snake player"""

    def _reset(self, ip_address: str, *args, **kwargs):
        """BaseSnakePlayer reset, but it has more stuff"""

        self.ip_address = ip_address
        super()._reset(*args, **kwargs)

    def get_data(self) -> dict:
        """Get data for updating the client"""

        return {
            "identifier": self.identifier,
            "ip_address": self.ip_address,
            "pos": self.pos,
            "length": self.length,
            "direction": self.direction,
        }

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


@server.on("leave")
def on_client_leave(client_data):
    Logger.log(
        f"{client_data.name} ({hisock.iptup_to_str(client_data.ip)})"
        " disconnected from the server"
    )

    # Remove player
    for player in snake_game.players_online:
        if player.identifier == client_data.name:
            snake_game.players_online.remove(player)
            break


@server.on("request_data")
def update_clients_with_data():
    server.send_all_clients("update_data", snake_game.get_data())


### Widgets / GUI ###
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

        widgets: list = [
            PlayersListWidget(),
            ServerInfoWidget(),
            ServerStatusMesagesWidget(),
        ]

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


class ServerInfoWidget(ServerWidget):
    """Widget for telling information about the server"""

    def __init__(self):
        super().__init__(
            pos=(GUI_CONFIG["widget_padding"], GUI_CONFIG["window_size"][1] // 2),
            size=(
                GUI_CONFIG["window_size"][0] // 4 * 1,
                GUI_CONFIG["window_size"][1] // 2 - GUI_CONFIG["widget_padding"],
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
            "mutable": [None, None],
        }
        self.update(do_check=False)

    def update(self, do_check: bool = True):
        if (not do_check) or snake_game.uptime_changed:
            uptime_text_widget = self.create_text(
                f"Uptime: {str(timedelta(seconds=snake_game.uptime))!s}", offset=5
            )
            self.text_widgets["mutable"][0] = uptime_text_widget
            if CONFIG["verbose"]:
                Logger.log(f"Created text widget for server uptime")

            self.text_widgets["mutable"][0] = uptime_text_widget

        time_next_tick_text = self.create_text(
            f"Time until next tick: {str(round(snake_game.time_next_tick, 1)).zfill(3)} ms",
            offset=6,
        )
        self.text_widgets["mutable"][1] = time_next_tick_text

    def draw(self):
        super().draw()

        for text_list in self.text_widgets.values():
            for text in text_list:
                text.draw()


class ServerStatusMesagesWidget(ServerWidget):
    """
    Widget for showing status messages about the current game,
    not just stats about the server.
    """

    def __init__(self):
        super().__init__(
            pos=(
                (GUI_CONFIG["widget_padding"] * 2)
                + (GUI_CONFIG["window_size"][0] // 4),
                GUI_CONFIG["widget_padding"],
            ),
            size=(
                (GUI_CONFIG["window_size"][0] // 4 * 3)
                - (GUI_CONFIG["widget_padding"] * 3),
                GUI_CONFIG["window_size"][1] - (GUI_CONFIG["widget_padding"] * 2),
            ),
            identifier="server status messages widget",
        )

        self.text_widgets: dict = {
            "immutable": [self.create_text("Server logs", offset=0)],
            "mutable": [],
        }
        self.update()

    def update(self):
        ...

    def add_text(self, text: str):
        # Add wrapping text
        if len(self.text_widgets["mutable"]) == 0:
            y_offset = self.padding
        else:
            y_offset = (
                self.text_widgets["mutable"][-1].ending_y_pos
                - (self.padding * 2)
                - len(self.text_widgets["mutable"])
            )

        text_wrapped = WrappedText(
            text=text,
            max_chars=80,
            pos=(
                self.pos[0] + self.size[0] // 2,
                self.pos[1] + (len(self.text_widgets["mutable"]) + self.text_size),
            ),
            y_offset=y_offset,
            text_size=self.text_size,
            text_color=self.text_color,
        )

        self.text_widgets["mutable"].append(text_wrapped)

    def draw(self):
        super().draw()

        for text_list in self.text_widgets.values():
            for text in text_list:
                text.draw()

    def scroll(self, scroll_by: int):
        for text in self.text_widgets["mutable"]:
            text.scroll(
                min_y=self.text_widgets["immutable"][0].text_rect.bottom,
                scroll_by=scroll_by,
            )

            # Clean up if no text left
            # if len(text.texts) == 0:
            # self.text_widgets["mutable"].pop(0)

    @property
    def needs_scroll(self):
        """Implies there is already a message"""

        return self.text_widgets["mutable"][-1].ending_y_pos >= (
            self.size[1] + self.pos[1]
        )

    @property
    def scroll_by(self):
        """Implies there is already a message"""

        return self.text_widgets["mutable"][-1].ending_y_pos - (
            self.size[1] + self.pos[1]
        )


### Override stdout ###
class StdOutOverride:
    def __init__(self, _file: TextIOWrapper):
        self.file = _file

    def write(self, text: str):
        self.file.write(text)
        if text != "\n":
            self.log_to_widget(text)

    def flush(self):
        self.file.flush()

    def log_to_widget(self, text: str):
        server_win.widgets[2].add_text(text)

        # Scrolling
        if server_win.widgets[2].needs_scroll:
            server_win.widgets[2].scroll(scroll_by=server_win.widgets[2].scroll_by)


sys.stdout = StdOutOverride(sys.stdout)

### Main ###
server_win = ServerWindow()
server.start()


def run_pygame_loop():
    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return False

        if event.type == pygame.KEYDOWN:
            # Debug!!!
            if event.key == pygame.K_SPACE:
                snake_game.players_online.append(
                    ServerSnakePlayer(
                        default_pos=(0, 0),
                        default_length=1,
                        identifier="Testing!",
                        ip_address=("192.168.86.60", 64012),
                    )
                )

            elif event.key == pygame.K_r:
                for player in snake_game.players_online:
                    player.reset()

            Logger.log(f"{chr(event.key) if event.key < 128 else event.key} pressed")

    # Update
    server_win.update()

    # Draw
    server_win.draw()
    pygame.display.flip()

    return True


def run():
    while True:
        try:
            if not run_pygame_loop():
                # Request to exit
                return pygame.quit()
            snake_game.run()
        except KeyboardInterrupt:
            print("\nExiting gracefully...")
            pygame.quit()
            return
        except Exception as e:
            Logger.log_error(e)
            return


if __name__ != "__main__":
    exit()

run()
del StdOutOverride
sys.stdout = sys.__stdout__

try:
    server.disconnect_all_clients(force=False)
    server.close()
except KeyboardInterrupt:
    print("\nForcing!")
    force_exit(1)
