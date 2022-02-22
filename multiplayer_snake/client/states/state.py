"""
Snake, but multiplayer
Created by sheepy0125
2021-11-16

State handling
"""

from multiplayer_snake.shared.config_parser import parse
from multiplayer_snake.shared.pygame_tools import Widget
from multiplayer_snake.client.states.game import GameState

CONFIG = parse()
GUI_CONFIG = CONFIG["gui"]


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


class State:
    """Handles the current state"""

    # current = ClientJoin() # NOSONAR
    # Testing XXX
    from multiplayer_snake.shared.common import hisock

    current = GameState(
        hisock.client.ThreadedHiSockClient(
            ("192.168.86.67", 6500),
            name=input("Username: "),
            group=None,
        )
    )


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


def update_state(state, *args, **kwargs):
    """Updates the current state"""

    State.current = state(*args, **kwargs)
