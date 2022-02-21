"""
Snake, but multiplayer
Created by sheepy0125
16/11/2021

Client game code
"""

### Setup ###
import pygame_gui
import constants
from common import hisock, pygame
from tools import Logger, get_public_ip, get_discriminator, check_username
from pygame_tools import GlobalPygame, Text, Button, CenterRect, Widget
from config_parser import parse
from shared_game import BaseSnakePlayer, SharedGame

CONFIG = parse()
GUI_CONFIG = CONFIG["gui"]
CLIENT_CONFIG = CONFIG["client"]

# Setup pygame
pygame.init()
GlobalPygame.window = pygame.display.set_mode(GUI_CONFIG["window_size"])
GlobalPygame.clock = pygame.time.Clock()
pygame.display.set_caption(f"{constants.__name__} Client (GUI)")

### Classes ###
class ClientSnakePlayer(BaseSnakePlayer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tail_color: list[int] = GUI_CONFIG["snek_tail"]
        self.head_color: list[int] = GUI_CONFIG["snek_head"]

    def draw(self):
        for tail_idx, tail_block in enumerate(self.tail):
            color = self.tail_color
            if tail_idx == 0:
                color = self.head_color

            pygame.draw.rect(
                GlobalPygame.window,
                color,
                width=SharedGame.grid_snap,
                height=SharedGame.grid_snap,
                center=tail_block,
            )


class SnakeClientGame:
    def __init__(
        self,
        username: str,
        discriminator: str,
        server_ip: str,
        server_port: int,
        client_hisock: hisock.client.HiSockClient,
    ):
        self.username = username
        self.discriminator = discriminator
        self.server_ip = server_ip
        self.server_port = server_port
        self.client_hisock = client_hisock


### Pygame States ###
def update_state(state, *args, **kwargs):
    """
    Updates the current state, and sets the next state
    """
    State.current = state(*args, **kwargs)


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


class ClientJoin(BaseState):
    def __init__(self):
        super().__init__(identifier="client join")

        # Variables
        self.username = ""
        self.discriminator = ""
        self.server_ip = ""

        # Setup
        self.gui_manager = pygame_gui.UIManager(GUI_CONFIG["window_size"])
        self.text_widgets: list[Text] = [
            self.create_text("Multiplayer Snake", 0.5, text_size=48),
            self.create_text(f"Created by {constants.__author__}", 5, text_size=12),
            self.create_text("Username", 3, text_size=36),
            self.create_text("Server IP (include port)", 5, text_size=36),
            self.create_text("Connect", 8, text_size=36),
        ]
        self.join_button = Button(
            (GUI_CONFIG["window_size"][0] // 2, self.text_widgets[-1].pos[1]),
            size=(200, 75),
            color="green",
        )

        # Text inputs
        self.text_inputs = {
            "username": pygame_gui.elements.UITextEntryLine(
                relative_rect=pygame.Surface(
                    (GUI_CONFIG["window_size"][0] * 0.4, 50)
                ).get_rect(center=(GUI_CONFIG["window_size"][0] // 2, 160)),
                manager=self.gui_manager,
            ),
            "server": pygame_gui.elements.UITextEntryLine(
                relative_rect=pygame.Surface(
                    (GUI_CONFIG["window_size"][0] * 0.4, 50)
                ).get_rect(center=(GUI_CONFIG["window_size"][0] // 2, 240)),
                manager=self.gui_manager,
            ),
        }
        for text_input in self.text_inputs.values():
            text_input.enable()

    def focus_current_textbox(self):
        for input in self.text_inputs.values():
            if input.relative_rect.collidepoint(pygame.mouse.get_pos()):
                input.focus()
                continue
            input.unfocus()

    def draw(self):
        self.join_button.draw()

        for widget in self.text_widgets:
            widget.draw()

        self.gui_manager.draw_ui(GlobalPygame.window)

    def handle_event(self, event: pygame.event.EventType):
        self.gui_manager.process_events(event)
        self.focus_current_textbox()
        # Handle button click
        if event.type == pygame.MOUSEBUTTONUP:
            mouse_pos = pygame.mouse.get_pos()
            if self.join_button.button_rect.collidepoint(*mouse_pos):
                self.join()

    def update(self):
        self.gui_manager.update(GlobalPygame.delta_time)
        self.gui_manager.draw_ui(GlobalPygame.window)
        GlobalPygame.window.fill(GUI_CONFIG["colors"]["background"])

    def join(self):
        Logger.log("Joining game")
        username = self.text_inputs["username"].text
        server_ip = self.text_inputs["server"].text

        if not check_username(username):
            Logger.fatal("Invalid username!")
            # TODO: status message
            return

        try:
            ip, port = hisock.utils.ipstr_to_tup(server_ip)
            hisock.utils.validate_ipv4((ip, port), require_port=True)
        except ValueError:
            Logger.fatal("Invalid IP!")
            # TODO: status message
            return

        Logger.log(f"Connecting: {username}@{ip} on port {port}")

        try:
            client = hisock.client.HiSockClient((ip, port), name=username, group=None)
            # New state
            update_state(GameState, client)
        except Exception as e:
            Logger.log_error(e)
            return


class GameState(BaseState):
    def __init__(self, client: hisock.client.ThreadedHiSockClient):
        super().__init__(identifier="game")

        self.client = client

    # TODO: everything


class State:
    """Handles the current state"""

    current = ClientJoin()


def run_pygame_loop():
    for event in pygame.event.get():
        State.current.handle_event(event)
        if event.type == pygame.QUIT:
            # TODO: Handle this
            exit(0)

    State.current.update()
    State.current.draw()
    GlobalPygame.update()


def run():
    while True:
        try:
            run_pygame_loop()
        except BrokenPipeError:
            # This is raised when the server is closed
            print("\nThe server has stopped, exiting!")
            raise
        except (KeyboardInterrupt, SystemExit):
            print("\nExiting gracefully", end="... ")
            if isinstance(State.current, GameState):
                State.current.client.send("leave")
                State.current.client.close()
            raise
        # except Exception as error:
        #   Logger.log_error(error)
        #   break


if __name__ == "__main__":
    run()
