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
class WaitingSubstate(BaseState):
    """
    This state is for when the game state is waiting for something
    It can be hidden in the background without being killed
    """

    def __init__(self, texts: list[str], *args, **kwargs):
        super().__init__(identifier="waiting", *args, **kwargs)

        ### Setup text ###
        self.text_widgets = []
        self.change_texts(texts)

        ### Setup rainbow background ###
        self.rainbow_color_increase = [True for _ in range(3)]
        self.background_color = GUI_CONFIG["colors"]["background"]
        self.background_color_display = self.background_color

        ### Setup variables ###
        self.active = False

    def change_texts(self, texts: list[str]):
        """Change the text to display. Each string in the list is a line of text."""

        self.text_widgets = [
            self.create_text(text, offset=0.5 + text_idx, text_size=48)
            for text_idx, text in enumerate(texts)
        ]

    def update(self):
        if not self.active:
            return

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
        if not self.active:
            return

        GlobalPygame.window.fill(self.background_color_display)

        for widget in self.text_widgets:
            widget.draw()
