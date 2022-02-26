"""
Snake, but multiplayer
Created by sheepy0125
2022-02-21

Client join state code
"""

### Setup ###
from multiplayer_snake.shared.common import pygame, Logger, hisock
from multiplayer_snake.client.states.state import BaseState, update_state
from multiplayer_snake.client.client import ClientSnakePlayer

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
        self.update = False

        @client.on("update")
        def update(self, data: dict):
            """Called every frame"""

            self.our_position = data["position"]
            self.our_direction = data["direction"]
            self.other_position = data["other_position"]
            self.other_direction = data["other_direction"]
            self.tail_length = data["tail_length"]
            self.update = True

    def handle_event(self, event: pygame.event.EventType):
        # Get keyboard input
        if event.type == pygame.KEYDOWN:
            key_pressed = pygame.key.get_pressed()
            if key_pressed in self.key_enum:
                self.next_move = self.key_enum[key_pressed]

    def update(self):
        if not self.update:
            return
        self.update = False

        # Our snake
        self.snake.update(self.our_position, self.our_direction, self.tail_length)

    def close(self):
        self.client.close(emit_leave=True)
