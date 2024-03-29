"""
Snake, but multiplayer
Created by sheepy0125
2022-02-21

Client join state code
"""

### Setup ###
from multiplayer_snake.shared.common import pygame, Logger, hisock, ClientInfo
from multiplayer_snake.shared.config_parser import parse
from multiplayer_snake.shared.shared_game import SharedGame
from multiplayer_snake.shared.pygame_tools import GlobalPygame
from multiplayer_snake.shared.hisock_tools import GlobalHiSock, hisock_callback, send
from multiplayer_snake.client.states.state import BaseState
from multiplayer_snake.client.snake import ClientSnakePlayer
from multiplayer_snake.client.food import ClientFood
from multiplayer_snake.client.states.waiting_substate import WaitingSubstate


CONFIG = parse()
GUI_CONFIG = CONFIG["gui"]

### Classes ###
class SentinelName:
    ...


class MultiplayerPlayer:
    def __init__(
        self, name: str | None, snake: ClientSnakePlayer, waiting_rematch: bool = False
    ):
        self.name = name or SentinelName()
        self.waiting_rematch = waiting_rematch
        self.snake = snake

        # Should be updated by first update, it's okay to set them to be None
        self.position: tuple | None = None
        self.direction: str | None = None
        self.tail: list | None = None

    def update(self, data: dict):
        """Updates data with that from the server "update" event"""

        self.position = data["pos"]
        self.direction = data["direction"]
        self.tail = data["tail"]
        self.snake.update(self.position, self.direction, self.tail)

    @property
    def exists(self):
        return not isinstance(self.name, SentinelName)


### States ###
class GameState(BaseState):
    """
    Game state
    Handles the HiSock connection, snake game, and can have the following substates:
    - WaitingPlayerJoinState
    These substates won't be set through the global state, instead being drawn in this
    state, so the HiSock connection can remain.
    """

    def __init__(self, client: hisock.client.ThreadedHiSockClient, *args, **kwargs):
        super().__init__(identifier="game", *args, **kwargs)

        ### HiSock setup ###
        GlobalHiSock.connection = client
        self.client = GlobalHiSock.connection
        self.client.start(callback=hisock_callback)
        # Change our name
        name: str = self.client.recv("join_response", recv_as=dict)["username"]
        self.client.change_name(name)

        ### Directions ###
        # Key enums
        self.key_enum = {
            pygame.K_w: "up",
            pygame.K_s: "down",
            pygame.K_a: "left",
            pygame.K_d: "right",
            pygame.K_UP: "up",
            pygame.K_DOWN: "down",
            pygame.K_LEFT: "left",
            pygame.K_RIGHT: "right",
        }
        self.rev_key_enum = {
            "up": "down",
            "down": "up",
            "left": "right",
            "right": "left",
        }
        # Corresponds to how many players have joined
        self.default_directions = [
            "right",
            "left",
        ]
        self.next_move: str
        # Default direction, will be changed by `_on_game_started`
        self.default_next_move: str | None = None

        ### Setup players ###
        self.players = {
            "self": MultiplayerPlayer(
                name=name,
                snake=ClientSnakePlayer(
                    head_color=GUI_CONFIG["colors"]["snek_one_head"],
                    tail_color=GUI_CONFIG["colors"]["snek_one_tail"],
                ),
            ),
            "other": MultiplayerPlayer(
                # We don't know if they've connected yet.
                # We'll find that out if the server sends a join response with
                # a list of player data...s
                name=None,
                snake=ClientSnakePlayer(
                    head_color=GUI_CONFIG["colors"]["snek_two_head"],
                    tail_color=GUI_CONFIG["colors"]["snek_two_tail"],
                ),
            ),
        }

        ### Setup game and board ###
        self.foods = []
        self.grid = Grid()

        ### Update data ###
        self.update_called = False
        self.update_data: dict

        ### Substates ###
        self.waiting_substate = WaitingSubstate(["Waiting to connect..."])
        self.waiting_substate.active = True

        ### HiSock listeners ###
        @client.on("player_connect")
        def _on_player_connect(player_data: list):
            num_of_players = len(player_data)

            if num_of_players == 1:
                return

            # Find the other player's name
            for player in player_data:
                player_name = player["identifier"]
                if player_name == self.players["self"].name:
                    continue
                # Found the other player's name
                self.players["other"].name = player_name
                break
            else:
                Logger.warn("Players have the same name, this shouldn't happen")
                self.players["other"].name = self.players["self"].name

            self.waiting_substate.active = False

        @client.on("game_started")
        def _on_game_started(default_directions: dict):
            self.default_next_move = default_directions[name]
            self.next_move = self.default_next_move

        @client.on("update")
        def _update(data: dict):
            """Called every frame"""

            self.update_called = True

            self.update_data = data
            self.update()

            # Send our data
            send(
                client.send,
                "update",
                {"direction": self.next_move},
            )

        @client.on("force_disconnect")
        def _on_leave():
            self.change_waiting_substate(["You've been kicked by the server!"])

        @client.on("client_disconnect")
        def _on_client_leave(client_data: ClientInfo):
            Logger.verbose(f"Client disconnect received: {client_data!s}")
            # Was it us? If so, we don't need to worry about it
            # as "force_disconnect" will handle that
            if client_data.name == self.players["self"].name:
                return

            # It wasn't us, so now there's one player
            self.change_waiting_substate(
                [
                    "The other player left!",
                    "",
                    "Waiting for another",
                    "player to join...",
                ]
            )

        # Everything is ready!
        # State that we're ready for receiving events
        send(client.send, "ready_for_events")

        self.change_waiting_substate(["Waiting for the other", "player to join..."])

    def change_waiting_substate(self, texts: list[str], activate: bool = True):
        self.waiting_substate.change_texts(texts)
        if activate:
            self.waiting_substate.active = True

    @property
    def players_connected(self) -> int:
        """Returns how many players are connected"""

        if self.players["other"].exists:
            return 2
        return 1

    def handle_event(self, event: pygame.event.EventType):
        if self.players_connected < 2:
            return

        # Get keyboard input
        if event.type == pygame.KEYDOWN and event.key in self.key_enum:
            next_move = self.key_enum[event.key]
            # Prevent the next move if it will cause the snake to go inside itself
            if (
                len(self.players["self"].tail)
                == 1  # We can move freely if we are just a head
                or self.rev_key_enum[next_move] != self.players["self"].direction
            ):
                self.next_move = next_move

    def update(self):
        self.waiting_substate.update()

        if not self.update_called:
            return

        # Update players
        player_data = self.update_data["players"]
        for player in self.players.values():
            # Ensure player exists
            if player.name not in player_data:
                # We'll handle the disconnection in a bit
                Logger.verbose(f"{player.name} doesn't exist, probably disconnected")
                continue
            player.update(player_data[player.name])

        # Update foods
        food_data = self.update_data["foods"]
        self.foods = []
        for food in food_data:
            self.foods.append(
                ClientFood(
                    tuple(food["pos"][i] * SharedGame.grid_snap for i in range(2))
                )
            )

        self.update_called = False

    def draw(self):
        ### Draw substates if needed ###
        if self.waiting_substate.active:
            self.waiting_substate.draw()
            return

        GlobalPygame.window.fill("black")
        # Grid
        self.grid.draw()
        GlobalPygame.window.blit(self.grid.grid_surf, (0, 0))
        # Draw the snakes
        for player in self.players.values():
            player.snake.draw()
        # Draw the foods
        for food in self.foods:
            food.draw()

    def close(self):
        self.client.close(emit_leave=True)


class Grid:
    """
    A simple grid that uses the information stored in the
    :class:`SharedGame` class
    """

    def __init__(self):
        self.grid_surf = pygame.Surface(
            (SharedGame.window_width, SharedGame.window_height)
        )

    def draw(self):
        # Draw lines onto the surface
        for row in range(0, SharedGame.width):
            pygame.draw.line(
                self.grid_surf,
                GUI_CONFIG["colors"]["grid"]["line"],
                ((row + 1) * SharedGame.grid_snap, 0),
                ((row + 1) * SharedGame.grid_snap, SharedGame.window_height),
            )
            for column in range(0, SharedGame.height):
                pygame.draw.line(
                    self.grid_surf,
                    GUI_CONFIG["colors"]["grid"]["line"],
                    (0, (column + 1) * SharedGame.grid_snap),
                    (SharedGame.window_width, (column + 1) * SharedGame.grid_snap),
                )
