"""
Snake, but multiplayer
Created by sheepy0125
2022-08-06

Waiting for player to join state
"""

### Setup ###
from random import randint
from multiplayer_snake.client.states.state import BaseState, GUI_CONFIG
from multiplayer_snake.shared.pygame_tools import GlobalPygame

### States ###
class WaitingPlayerJoinState(BaseState):
    """
    This state is for when the player is waiting for another player to join
    It can be killed at any time if a player joined
    """

    def __init__(self, *args, **kwargs):
        super().__init__(identifier="waiting player join", *args, **kwargs)

        ### Setup text ###
        self.text_widgets = [
            self.create_text("Waiting for another", 0.5, text_size=48),
            self.create_text("player to join!", 1.5, text_size=48),
        ]

        ### Setup rainbow background ###
        self.rainbow_color_increase = [True for _ in range(3)]
        self.background_color = GUI_CONFIG["colors"]["background"]
        self.background_color_display = self.background_color

    def update(self):
        # Change rainbow background color
        idx_to_change = randint(1, 3) - 1
        self.background_color[idx_to_change] += (
            0.5 if self.rainbow_color_increase[idx_to_change] else -0.5
        )
        # Disallow overflow and underflow
        if self.background_color[idx_to_change] >= 254:
            self.rainbow_color_increase[idx_to_change] = False
        elif self.background_color[idx_to_change] <= 30:
            self.rainbow_color_increase[idx_to_change] = True
        self.background_color_display = [int(value) for value in self.background_color]

    def draw(self):
        GlobalPygame.window.fill(self.background_color_display)

        for widget in self.text_widgets:
            widget.draw()
