"""
Snake, but multiplayer
Created by sheepy0125
2021-11-16

Client game code
"""

### Setup ###
from typing import Callable
from multiplayer_snake import constants
from multiplayer_snake.shared.common import pygame, Logger
from multiplayer_snake.shared.config_parser import parse
from multiplayer_snake.shared.pygame_tools import GlobalPygame, DialogWidget
from multiplayer_snake.client.states.state import state, update_state
from multiplayer_snake.client.states.state_info import ClientJoinState

CONFIG = parse()
GUI_CONFIG = CONFIG["gui"]
CLIENT_CONFIG = CONFIG["client"]

# Setup pygame
pygame.init()
GlobalPygame.window = pygame.display.set_mode(GUI_CONFIG["window_size"])
GlobalPygame.clock = pygame.time.Clock()
pygame.display.set_caption(f"{constants.__name__} Client (GUI)")

### GUI ###
class ClientWindow:
    """
    Client window, renders on-top of the state.
    Used for displaying error messages and such.
    """

    def __init__(self):
        self.dialogs = {"error": None}

    def error_message(self, message: str):
        """Show an error message"""

        def close_dialog():
            self.dialogs["error"] = None
            # Stop everything!
            raise KeyboardInterrupt

        self.dialogs["error"] = DialogWidget(
            message, identifier="error dialog", text_size=12, close=close_dialog
        )

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

    def handle_event(self, event: pygame.event.EventType):
        if not any(self.dialogs.values()):
            state.current.handle_event(event)

    def update(self):
        for dialog in self.dialogs.values():
            if dialog is None:
                continue
            dialog.update()

        if not any(self.dialogs.values()):
            state.current.update()

    def draw(self):
        state.current.draw()

        for dialog in self.dialogs.values():
            if dialog is None:
                continue
            dialog.draw()


### Main ###
client_win = ClientWindow()
state.display_dialog = client_win.display_dialog
update_state(ClientJoinState)


def error_handler(error: Exception):
    client_win.error_message(Logger.log_error(error))


### Run ###
def run_pygame_loop():
    GlobalPygame.window.fill("black")

    for event in pygame.event.get():
        state.current.handle_event(event)
        if event.type == pygame.QUIT:
            return False

    client_win.update()
    client_win.draw()
    GlobalPygame.update()

    return True


def run():
    while True:
        try:
            if not run_pygame_loop():
                # Request to exit
                pygame.quit()
                raise KeyboardInterrupt
        except KeyboardInterrupt:
            print("\nExiting gracefully", end="... ")
            state.current.close()
            return
        except Exception as e:
            error_handler(e)


if __name__ == "__main__":
    run()
