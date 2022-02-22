"""
Snake, but multiplayer
Created by sheepy0125
2021-11-16

State handling
"""

### Setup ###
from multiplayer_snake.shared.config_parser import parse
from multiplayer_snake.shared.pygame_tools import Widget
from multiplayer_snake.shared.common import Logger, pygame


CONFIG = parse()
GUI_CONFIG = CONFIG["gui"]


### Widgets ###
class ClientWidget(Widget):
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


### States ###


class BaseState(Widget):
    def __init__(self, identifier: str | None = None, *args, **kwargs):
        # Colors and stuff
        text_size = GUI_CONFIG["text_size"]
        text_color = GUI_CONFIG["colors"]["widget"]["text"]
        padding = GUI_CONFIG["widget_padding"]
        widget_color = GUI_CONFIG["colors"]["widget"]["background"]
        border_color = GUI_CONFIG["colors"]["widget"]["border"]

        # Full screen
        pos = (0, 0)
        size = GUI_CONFIG["window_size"]

        # Identifier
        if identifier is None:
            identifier = "unknown state"

        super().__init__(
            pos=pos,
            size=size,
            text_size=text_size,
            text_color=text_color,
            padding=padding,
            widget_color=widget_color,
            border_color=border_color,
            identifier=identifier,
            *args,
            **kwargs,
        )

        if CONFIG["verbose"]:
            Logger.log(f"Created {self.identifier} state")

    def handle_event(self, _: pygame.event.Event):
        Logger.warn(f"State {self.identifier} has no event handler")


class State:
    """Handles the current state"""

    current = BaseState()


def update_state(state, *args, **kwargs):
    """Updates the current state"""

    State.current = state(*args, **kwargs)
