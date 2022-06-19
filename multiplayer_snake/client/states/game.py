"""
Snake, but multiplayer
Created by sheepy0125
2022-02-21

Client join state code
"""

### Setup ###
from multiplayer_snake.shared.common import pygame, Logger, hisock
from multiplayer_snake.shared.config_parser import parse
from multiplayer_snake.shared.shared_game import SharedGame
from multiplayer_snake.shared.pygame_tools import GlobalPygame
from multiplayer_snake.client.states.state import BaseState, update_state
from multiplayer_snake.client.snake import ClientSnakePlayer
from multiplayer_snake.client.food import ClientFood

CONFIG = parse()
GUI_CONFIG = CONFIG["gui"]

### States ###
class GameState(BaseState):
    def __init__(self, client: hisock.client.ThreadedHiSockClient, *args, **kwargs):
        super().__init__(identifier="game", *args, **kwargs)

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

        # next commit :eyes:
        # self.waiting_other_player = True

        self.foods = []
        self.snake = ClientSnakePlayer(
            head_color=GUI_CONFIG["colors"]["snek_one_head"],
            tail_color=GUI_CONFIG["colors"]["snek_one_tail"],
        )
        self.other_snake = ClientSnakePlayer(
            head_color=GUI_CONFIG["colors"]["snek_two_head"],
            tail_color=GUI_CONFIG["colors"]["snek_two_tail"],
        )
        self.update_called = False
        self.grid = Grid()

        self.client = client
        self.client.start()
        # Default direction, can be changed by `on_player_connect`
        # XXX This is kinda hacky, consider refactoring
        self.next_move = "left"
        self.default_next_move = "left"

        self.name = client.recv("join_response", recv_as=dict)["username"]
        self.other_name = "NULL"  # XXX This is kinda hacky, consider refactoring

        @client.on("player_connect")
        def on_player_connect(player_data: list):
            # XXX There's probably a better way to do this
            self.other_name = player_data[-1]["identifier"]
            if len(player_data) == 1:
                # We're the first player, face right instead of left
                self.next_move = "right"
                self.default_next_move = "right"

        @client.on("game_started")
        def on_game_started(data: dict):
            players = data["players"]
            self.other_name = players[players.index(self.name) - 1]
            self.next_move = self.default_next_move

        @client.on("update")
        def update(data: dict):
            """Called every frame"""

            player_data = data["players"]

            our_data = player_data[self.name]
            self.our_position = our_data["pos"]
            self.our_direction = our_data["direction"]
            self.our_tail = our_data["tail"]

            other_data = player_data[self.other_name]
            self.other_position = other_data["pos"]
            self.other_direction = other_data["direction"]
            self.other_tail = other_data["tail"]

            food_data = data["foods"]
            self.foods = []
            for food in food_data:
                self.foods.append(
                    ClientFood(
                        tuple(food["pos"][i] * SharedGame.grid_snap for i in range(2))
                    )
                )

            self.update_called = True

            # Send our data
            client.send(
                "update", {"direction": self.next_move, "identifier": self.name}
            )

    def handle_event(self, event: pygame.event.EventType):
        # Get keyboard input
        if event.type == pygame.KEYDOWN and event.key in self.key_enum:
            next_move = self.key_enum[event.key]
            # Prevent the next move if it will cause the snake to go inside itself
            if (
                len(self.our_tail) == 1  # We can move freely if we are just a head
                or self.rev_key_enum[next_move] != self.our_direction
            ):
                self.next_move = next_move

    def update(self):
        if not self.update_called:
            return

        self.update_called = False

        print(f"Updating: {self.our_position}")

        # Update the snake
        self.snake.update(self.our_position, self.our_tail, self.our_direction)

        # Update the other snake
        self.other_snake.update(
            self.other_position, self.other_tail, self.other_direction
        )

        self.snake.update(self.our_position, self.our_direction, self.our_tail)
        self.other_snake.update(
            self.other_position, self.other_direction, self.other_tail
        )

    def draw(self):
        GlobalPygame.window.fill("black")
        # Grid
        self.grid.draw()
        GlobalPygame.window.blit(self.grid.grid_surf, (0, 0))
        # Draw the snakes
        self.snake.draw()
        self.other_snake.draw()
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
                ((row + 0.5) * SharedGame.grid_snap, 0),
                ((row + 0.5) * SharedGame.grid_snap, SharedGame.window_height),
            )
            for column in range(0, SharedGame.height):
                pygame.draw.line(
                    self.grid_surf,
                    GUI_CONFIG["colors"]["grid"]["line"],
                    (0, (column + 0.5) * SharedGame.grid_snap),
                    (SharedGame.window_width, (column + 0.5) * SharedGame.grid_snap),
                )
