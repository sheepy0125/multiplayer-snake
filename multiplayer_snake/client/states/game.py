"""
Snake, but multiplayer
Created by sheepy0125
2022-02-21

Client join state code
"""

### Setup ###
from multiplayer_snake.shared.common import pygame, Logger
from multiplayer_snake.client.states.state import State, update_state

### States ###
class GameState(BaseState):
    def __init__(self, client: hisock.client.ThreadedHiSockClient):
        super().__init__(identifier="game")

        self.client = client

    def handle_event(self, event: pygame.event.EventType):
        ...
