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

CONFIG = parse()
GUI_CONFIG = CONFIG["gui"]

### States ###
class GameState(BaseState):
    def __init__(self, client: hisock.client.ThreadedHiSockClient):
        super().__init__(identifier="game")

        self.key_enum = {
            pygame.K_w: "up",
            pygame.K_s: "down",
            pygame.K_a: "left",
            pygame.K_d: "right",
            pygame.K_UP: "up",
            pygame.K_DOWN: "up",
            pygame.K_LEFT: "left",
            pygame.K_RIGHT: "right",
        }

        self.client = client
        self.snake = ClientSnakePlayer()
        self.other_snake = ClientSnakePlayer()
        self.grid = Grid()
        self.update_called = False

        @client.on("update")
        def update(data: dict):
            """Called every frame"""

            self.our_position = data["position"]
            self.our_direction = data["direction"]
            self.other_position = data["other_position"]
            self.other_direction = data["other_direction"]
            self.tail_length = data["tail_length"]
            self.update_called = True

    def handle_event(self, event: pygame.event.EventType):
        # Get keyboard input
        if event.type == pygame.KEYDOWN:
            key_pressed = pygame.key.get_pressed()
            if key_pressed in self.key_enum:
                self.next_move = self.key_enum[key_pressed]

    def update(self):
        if not self.update_called:
            return
        self.update_called = False

        # Our snake
        self.snake.update(self.our_position, self.our_direction, self.tail_length)

    def draw(self):
        GlobalPygame.window.fill("black")
        # Grid
        self.grid.draw()
        GlobalPygame.window.blit(self.grid.grid_surf, (0, 0))
        # Draw the snakes
        self.snake.draw()
        self.other_snake.draw()

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
        for row in range(0, SharedGame.height):
            pygame.draw.line(
                self.grid_surf,
                GUI_CONFIG["colors"]["grid"]["line"],
                (row * SharedGame.grid_snap, 0),
                (row * SharedGame.grid_snap, SharedGame.window_height),
            )
            for column in range(0, SharedGame.width):
                pygame.draw.line(
                    self.grid_surf,
                    GUI_CONFIG["colors"]["grid"]["line"],
                    (0, column * SharedGame.grid_snap),
                    (SharedGame.window_width, column * SharedGame.grid_snap),
                )
