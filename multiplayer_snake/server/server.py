"""
Snake, but multiplayer
Created by sheepy0125
2021-11-14

Server side code!
"""

### Setup ###
from typing import Callable
from time import time
from datetime import timedelta
from os import _exit as force_exit
from io import TextIOWrapper
from random import randint
from threading import Thread
import sys
from multiplayer_snake import constants
from multiplayer_snake.shared.pygame_tools import DialogWidget
from multiplayer_snake.shared.hisock_tools import GlobalHiSock, send, hisock_callback
from multiplayer_snake.shared.common import (
    hisock,
    ClientInfo,
    pygame,
    Logger,
)  # pylint: disable=no-name-in-module
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
    Button,
)
from multiplayer_snake.shared.config_parser import parse
from multiplayer_snake.shared.shared_game import BaseSnakePlayer, SharedGame

CONFIG = parse()
GUI_CONFIG = CONFIG["gui"]
SERVER_CONFIG = CONFIG["server"]

# Setup pygame
pygame.init()
GlobalPygame.window = pygame.display.set_mode(GUI_CONFIG["window_size"])
pygame.display.set_caption(f"{constants.__name__} Server (GUI)")

# Setup hisock
Logger.verbose("Setting up HiSock server")
try:
    GlobalHiSock.connection = hisock.server.ThreadedHiSockServer(
        ("127.0.0.1", CONFIG["server"]["port"]),
        max_connections=2,
        cache_size=1,
    )
except Exception as e:
    Logger.fatal("Failed to start server!")
    Logger.log_error(e)
    sys.exit(1)

server = GlobalHiSock.connection

### Classes ###
class GameAlreadyRunningError(Exception):
    ...


class SnakeGame:
    """Handles everything that will be sent to the clients"""

    def __init__(self):
        self.num_players = 2
        self.players_online: list[ServerSnakePlayer] = []

        self.round = 0
        self.uptime: int = 0  # Seconds
        self.uptime_changed: bool = False  # For the GUI

        self._reset()

        self.default_positions = (
            (5, round(((SharedGame.height / 2) - 1), ndigits=1)),
            (SharedGame.width - 5, round(((SharedGame.height / 2) - 1), ndigits=1)),
        )
        self.default_directions = ("right", "left")

    def _reset(self):
        Logger.log("Resetting game")
        self.frames: int = 0
        self.running: bool = False
        self.start_time: int = 0  # Unix timestamp
        self.last_update_time: float = 0.0  # Unix timestamp
        self.time_next_tick: float = 0.0  # Milliseconds
        self.food = []
        for player in self.players_online:
            player.reset()

    def get_data(self) -> dict:
        """Get data for updating the clients"""

        # Get the data
        return {
            "players": {
                player.identifier: player.get_data() for player in self.players_online
            },
            "foods": [food.get_data() for food in self.food],
            "round": self.round,
            "uptime": self.uptime,
            "uptime_changed": self.uptime_changed,
        }

    def get_player_idx(self, identifier: str) -> int:
        """Gets an index for a player with an identifier. Returns -1 if not found."""

        for idx, player in enumerate(self.players_online):
            if player.identifier == identifier:
                return idx
        return -1

    def update_player(self, player_identifier: str, direction: str):
        """Update a player"""

        player_idx = self.get_player_idx(player_identifier)
        self.players_online[player_idx].direction = direction

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
        if time_next_tick >= 0:
            return

        self.frames += 1

        self.last_update_time += SERVER_CONFIG["time_until_update"]

        # Update players
        for player_idx, player in enumerate(self.players_online):
            # Update food
            for food in self.food:
                if food.update(player):
                    player.touched_food()

            player.update(self.players_online[player_idx - 1])

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

        Logger.log("Starting game")

        self.food = [ServerFood(), ServerFood()]
        self.running = True
        self.start_time = int(time())
        self.last_update_time = time()

        # Alert everyone that the game has started
        send(
            server.send_all_clients,
            "game_started",
            {"players": [player.identifier for player in self.players_online]},
        )

    def pause(self):
        """Pause the game"""

        if not self.running:
            return

        Logger.log("Pausing game")
        self.running = False

    def stop(self):
        """Stop the game. Assumes the game has been paused."""

        self._reset()

    def add_player(self, ip_address: str, username: str) -> bool:
        """Adds a player to the game, returns if valid"""

        # Too many players already
        if len(self.players_online) > self.num_players:
            return False

        # Username isn't good
        # The username will have a 4 digit discriminator with a hashtag.
        # Hashtags aren't allowed except for the discriminator.
        if not check_username(username[:-5]):
            return False

        # Everything seems fine, add the player

        # Get the default position
        default_pos = self.default_positions[len(self.players_online)]
        default_dir = self.default_directions[len(self.players_online)]

        self.players_online.append(
            ServerSnakePlayer(
                default_pos=default_pos,
                default_dir=default_dir,
                default_length=1,
                identifier=username,
                ip_address=ip_address,
            )
        )

        Logger.verbose(f"Added player {username}")

        return True

    def snake_died(self, identifier: str, reason: str):
        Logger.log("The game has ended!")
        send(
            server.send_all_clients, "game_over", f"{identifier} died because {reason}"
        )
        self.stop()


snake_game = SnakeGame()


class ServerSnakePlayer(BaseSnakePlayer):
    """Server side snake player"""

    def _reset(self, ip_address: str, *args, **kwargs):
        """BaseSnakePlayer reset, but it has more stuff"""

        super()._reset(*args, **kwargs)

        Logger.verbose(f"Resetting {self.identifier} snake")

        self.ip_address = ip_address

        self.direction_velocity_enum = {
            "up": (0, -1),
            "down": (0, 1),
            "left": (-1, 0),
            "right": (1, 0),
        }

    def move(self):
        # Update position
        new_pos = [
            self.pos[dimension]
            + self.direction_velocity_enum[self.direction][dimension]
            for dimension in range(2)
        ]
        self.pos = new_pos

        self.tail.insert(0, self.pos)
        if len(self.tail) > self.length:
            self.tail.pop()

    def collision_checking(self, other_snake_object: "BaseSnakePlayer"):
        # Check if the snake is out of bounds
        if (self.pos[0] < 0 or self.pos[0] >= SharedGame.width) or (
            self.pos[1] < 0 or self.pos[1] >= SharedGame.height
        ):
            self.snake_died(reason="out of bounds")

        # Check if the snake is colliding with itself
        for pos in self.tail[1:]:
            if pos == self.pos:
                self.snake_died(reason="collided with self")

        # Check if the snake is colliding with the other snake
        for pos in other_snake_object.tail:
            if pos == self.pos:
                self.snake_died(reason="collided with other snake")

    def get_data(self) -> dict:
        """Get data for updating the client"""

        return {
            "identifier": self.identifier,
            "ip_address": self.ip_address,
            "pos": self.pos,
            "length": self.length,
            "direction": self.direction,
            "tail": self.tail,
        }

    def update(self, other_snake_player: BaseSnakePlayer):
        """Update the player"""
        self.move()
        self.collision_checking(other_snake_player)

    def snake_died(self, reason: str = "unknown"):
        super().snake_died(reason)
        snake_game.snake_died(identifier=self.identifier, reason=reason)


class ServerFood:
    """Server side food"""

    def __init__(self):
        self.respawn()

    def respawn(self):
        """Respawn the food"""

        self.pos = (
            randint(0, SharedGame.width - 1),
            randint(0, SharedGame.height - 1),
        )

    def get_data(self) -> dict:
        """Get data for updating the clients"""

        return {"pos": self.pos}

    def update(self, player: ServerSnakePlayer):
        """Update the food. Returns if the player ate the food"""

        # If the food is touched by a snake, respawn it
        if tuple(map(int, player.pos)) == tuple(map(int, self.pos)):
            Logger.log(f"{player.identifier} ate food")
            self.respawn()
            return True

        return False


### Server handlers ###
def _wait_for_ready_signal() -> bool:
    server.recv(recv_on="ready_for_events")
    return True


@server.on("join", threaded=True)
def on_client_join(client_data: ClientInfo):
    Logger.log(
        f"{client_data.name} ({hisock.iptup_to_str(client_data.ip)})"
        " connected to the server"
    )

    username = f"{client_data.name}#{get_discriminator()}"

    if not snake_game.add_player(client_data.ip, username):
        # Failed to join, disconnect player
        Logger.log("Disconnecting player...")
        server.disconnect_client(client_data)
        return

    send(server.send_client, client_data, "join_response", {"username": username})

    # If we send the player connect event too fast, then the client may not receive it
    # So, wait for the client to be ready
    # This also serves as a sort-of keepalive to see if the client acts normally and/or
    # doesn't die immediately
    timeout = 10  # seconds
    Logger.log(
        f"Blocking join thread until client {username} says they're ready... "
        f"timeout of {timeout} seconds"
    )
    waiting_ready_signal_thread = Thread(target=_wait_for_ready_signal)
    waiting_ready_signal_thread.start()
    start_time = time()
    waiting_ready_signal_thread.join(float(timeout))
    finished_waiting_time = time()
    if finished_waiting_time - start_time >= timeout - 0.25:
        Logger.log("It seems like they're dead, not going to block anymore")
        server.disconnect_client(client_data.ip)
        return
    Logger.log("They're ready! Continuing...")

    send(
        server.send_all_clients,
        "player_connect",
        [player.get_data() for player in snake_game.players_online],
    )


@server.on("leave")
def on_client_leave(client_data: ClientInfo):
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
    send(server.send_all_clients, "update", snake_game.get_data())


@server.on("update")
def on_client_update(client_data: ClientInfo, data: dict):
    player_identifier = client_data["name"]
    new_direction = data["direction"]
    snake_game.update_player(player_identifier, new_direction)


@server.on("name_change")
def on_name_change(client_data: ClientInfo, old_name: str, new_name: str):
    Logger.verbose(f"Name change: {old_name} -> {new_name}")
    # Check if the name change was sane
    for player in snake_game.players_online:
        if player.identifier == new_name:
            break
    else:
        Logger.fatal(
            f"{old_name} changed their name to {new_name}, "
            "but that's not a valid player name! Kicking!"
        )
        server.disconnect_client(client_data)


@server.on("*", threaded=True)
def on_wildcard(client_data: ClientInfo, command: str, data: str):
    Logger.warn(
        f"Wildcard command received from {client_data.ip}: {command} with data: {data}"
    )


### Widgets / GUI ###
class ServerWindow:
    """Handles all the widgets inside the window"""

    def __init__(self):
        """No params as this will use CONFIG"""

        self.widgets = self.create_widgets()
        self.dialogs = {"error": None}

        Logger.verbose("Server window created")

    @staticmethod
    def create_widgets() -> list:
        Logger.verbose("Creating widgets")

        widgets: list = [
            PlayersListWidget(),
            ServerInfoWidget(),
            ServerStatusMessagesWidget(),
        ]

        Logger.verbose(
            f"Created {len(widgets)} widgets: "
            f"{', '.join((repr(widget) for widget in widgets))}"
        )

        return widgets

    def error_message(self, message: str):
        """Show an error message"""

        def close_dialog():
            self.dialogs["error"] = None
            # Stop everything!
            raise KeyboardInterrupt

        self.dialogs["error"] = DialogWidget(
            message, text_size=12, identifier="error dialog", close=close_dialog
        )

        # Pause the game
        snake_game.pause()

    def display_dialog(
        self,
        identifier: str,
        message: str,
        center: bool = False,
        text_size: int = 12,
        close: Callable = lambda: None,
    ):
        """
        Displays a dialog. Will be called from a state.
        .. note::
           If you want to call error_message, raise an exception.
        """

        def _close():
            self.dialogs[identifier] = None
            close()

        self.dialogs[identifier] = DialogWidget(
            message,
            identifier=identifier,
            text_size=text_size,
            center=center,
            close=_close,
        )

    def update(self):
        """Updates all the widgets and dialogs"""

        for widget in self.widgets:
            widget.update()

        for dialog in self.dialogs.values():
            if dialog is None:
                continue
            dialog.update()

    def draw(self):
        """Draws all the widgets and the main window"""

        # Draw background
        GlobalPygame.window.fill(GUI_CONFIG["colors"]["background"])

        # Draw widgets
        for widget in self.widgets:
            widget.draw()

        # Draw dialogs
        for dialog in self.dialogs.values():
            if dialog is None:
                continue
            dialog.draw()


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

        Logger.verbose(f"Created {self.identifier} widget")

    def __repr__(self):
        return f"<ServerWidget identifier={self.identifier}>"


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
                self.create_text("Players online", offset=0, text_size=16),
            ],
            "mutable": [],
        }
        self.update(do_check=False)

    def update(self, do_check: bool = True):
        if do_check and (
            len(self.text_widgets["mutable"]) == len(snake_game.players_online) * 2
        ):
            return

        Logger.verbose(
            f"Updating players (players online: {len(snake_game.players_online)}, "
            f"players shown: {len(self.text_widgets['mutable']) // 2})"
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

            Logger.verbose(f"Created text widget for player snake {player.identifier}")

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
                self.create_text("Server status", offset=0, text_size=16),
                self.create_text(f"Local IP: {hisock.utils.get_local_ip()}", offset=2),
                self.create_text(f"Public IP: {get_public_ip()}", offset=3),
                self.create_text(f"Port: {CONFIG['server']['port']}", offset=4),
                Text(
                    "Stop and Reset",
                    pos=(
                        self.pos[0] + (self.size[0] // 2),
                        self.pos[1] + self.size[1] - 85,
                    ),
                    size=14,
                    color=self.text_color,
                    center=True,
                ),
                Text(
                    "Start/Pause",
                    pos=(
                        self.pos[0] + (self.size[0] // 2),
                        self.pos[1] + self.size[1] - 40,
                    ),
                    size=14,
                    color=self.text_color,
                    center=True,
                ),
            ],
            "mutable": [self.create_text("")] * 3,
        }

        self.start_stop_button = Button(
            pos=(
                self.pos[0] + (self.size[0] // 2),
                self.pos[1] + self.size[1] - 40,
            ),
            size=(self.size[0] // 4 * 3, 50),
            color="orange",
        )
        self.reset_button = Button(
            pos=(
                self.pos[0] + (self.size[0] // 2),
                self.pos[1] + self.size[1] - 85,
            ),
            size=(self.size[0] // 4 * 3, 50),
            color="orange",
        )

        self.update(do_check=False)

    def update(self, do_check: bool = True):
        if (not do_check) or snake_game.uptime_changed:
            uptime_text_widget = self.create_text(
                f"Uptime: {str(timedelta(seconds=snake_game.uptime))!s}", offset=5
            )
            self.text_widgets["mutable"][0] = uptime_text_widget

            frame_count_widget = self.create_text(
                f"Frames: {snake_game.frames}/"
                + str(
                    int(
                        (
                            snake_game.uptime
                            * (1 // (CONFIG["server"]["time_until_update"] * 0.95))
                        )
                    )
                )
                + " (estimate)",
                offset=6,
            )
            self.text_widgets["mutable"][1] = frame_count_widget

        if snake_game.running:
            time_next_tick_text = self.create_text(
                f"Next frame in: {str(round(snake_game.time_next_tick, 4)).zfill(6)} ms",
                offset=7,
            )
            self.text_widgets["mutable"][2] = time_next_tick_text

        if self.start_stop_button.check_pressed():
            if not snake_game.running:
                snake_game.start()
            else:
                snake_game.pause()

        if self.reset_button.check_pressed():
            # Don't allow reset if not stopped
            if snake_game.running:
                server_win.display_dialog(
                    identifier="reset_error",
                    message="The game must be paused first!",
                    center=True,
                    text_size=32,
                )
            else:
                snake_game._reset()

    def draw(self):
        super().draw()

        self.start_stop_button.draw()
        self.reset_button.draw()

        for text_list in self.text_widgets.values():
            for text in text_list:
                text.draw()


class ServerStatusMessagesWidget(ServerWidget):
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

        self.max_chars = (self.size[0] - (self.padding * 2)) // self.text_size * 2
        Logger.verbose(f"Max characters for logging: {self.max_chars}")

        self.text_widgets: dict = {
            "immutable": [self.create_text("Server logs", offset=0, text_size=16)],
            "mutable": [],
        }
        self.update()

    def update(self):
        sys.stdout.clear_buffer()

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
            max_chars=self.max_chars,
            pos=(
                self.pos[0] + self.padding,
                self.pos[1] + (len(self.text_widgets["mutable"]) + self.text_size),
            ),
            y_offset=y_offset,
            text_size=self.text_size,
            text_color=self.text_color,
            center=False,
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

    @property
    def needs_scroll(self):
        """Assumes there is already a message"""

        return self.text_widgets["mutable"][-1].ending_y_pos >= (
            self.size[1] + self.pos[1]
        )

    @property
    def scroll_by(self):
        """Assumes there is already a message"""

        return self.text_widgets["mutable"][-1].ending_y_pos - (
            self.size[1] + self.pos[1]
        )


### Override stdout ###
class StdOutOverride:
    def __init__(self, _file: TextIOWrapper):
        self.file = _file
        # Sometimes, what will happen is a message will be logged before the server
        # window is fully initialized
        # In that case, we need to put it in a buffer and output them later
        self.buffer = set()

    def write(self, text: str):
        self.file.write(text)

        if text != "\n":
            # Strip color
            for ansi_color in Logger.colors.values():
                text = text.replace(ansi_color, "")

            self.buffer.add(text)

    def flush(self):
        """Rarely used, but keep it"""

        self.file.flush()

    def log_to_widget(self, text: str) -> bool:
        """Returns whether the logging succeeded or not"""

        try:
            server_win.widgets[2].add_text(text)

            # Scrolling
            if server_win.widgets[2].needs_scroll:
                server_win.widgets[2].scroll(scroll_by=server_win.widgets[2].scroll_by)

            return True
        except NameError:
            self.buffer.add(text)
            return False

    def clear_buffer(self):
        while len(self.buffer) > 0:
            if not self.log_to_widget(self.buffer.pop()):
                break


sys.stdout = StdOutOverride(sys.stdout)

### Main ###
server_win = ServerWindow()

# Start HiSock server
def error_handler(error: Exception):
    server_win.error_message(Logger.log_error(error))


server.start(callback=hisock_callback, error_handler=error_handler)


def run_pygame_loop():
    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return False

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
                pygame.quit()
                return
            snake_game.run()
        except KeyboardInterrupt:
            print("\nExiting gracefully...")
            pygame.quit()
            return
        except Exception as e:  # pylint: disable=redefined-outer-name
            error_handler(e)


if __name__ != "__main__":
    Logger.verbose("Not running by self, exiting!")
    sys.exit()

Logger.verbose("Everything ready, running main loop!")
run()
Logger.verbose("Finished running!")
Logger.verbose("Deleting stdout override!")
del StdOutOverride
sys.stdout = sys.__stdout__

try:
    Logger.verbose("Closing server")
    server.close()
    Logger.verbose("Goodbye!")
except KeyboardInterrupt:
    print("\nForcing!")
    force_exit(1)
