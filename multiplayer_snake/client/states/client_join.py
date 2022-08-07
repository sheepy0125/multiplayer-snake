"""
Snake, but multiplayer
Created by sheepy0125
2022-02-21

Client join state code
"""

### Setup ###
from multiplayer_snake import constants
from multiplayer_snake.client.states.state import BaseState, GUI_CONFIG, update_state
from multiplayer_snake.client.states.state_info import GameState
from multiplayer_snake.shared.common import Logger
from multiplayer_snake.shared.pygame_tools import Button, GlobalPygame
from multiplayer_snake.shared.common import pygame_gui, pygame, hisock
from multiplayer_snake.shared.tools import check_username

### States ###
class ClientJoinState(BaseState):
    def __init__(self, *args, **kwargs):
        super().__init__(identifier="client join", *args, **kwargs)

        ### Setup input variables ###
        self.username = ""
        self.server_ip = ""

        ### Setup GUI ###
        self.gui_manager = pygame_gui.UIManager(GUI_CONFIG["window_size"])
        # Text widgets
        self.text_widgets = [
            self.create_text("Multiplayer Snake", 0.5, text_size=48),
            self.create_text(f"Created by {constants.__author__}", 5, text_size=12),
            self.create_text("Username", 3, text_size=36),
            self.create_text("Server IP (include port)", 5, text_size=36),
            self.create_text("Connect", 8, text_size=36),
        ]
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
        # Join button
        self.join_button = Button(
            (GUI_CONFIG["window_size"][0] // 2, self.text_widgets[-1].pos[1]),
            size=(200, 75),
            color="green",
        )

    def focus_current_textbox(self):
        for text_input in self.text_inputs.values():
            if text_input.relative_rect.collidepoint(pygame.mouse.get_pos()):
                text_input.focus()
                continue
            text_input.unfocus()

    def draw(self):
        GlobalPygame.window.fill(GUI_CONFIG["colors"]["background"])

        self.join_button.draw()

        for widget in self.text_widgets:
            widget.draw()

        self.gui_manager.draw_ui(GlobalPygame.window)

    def handle_event(self, event: pygame.event.EventType):
        self.gui_manager.process_events(event)
        self.focus_current_textbox()

    def update(self):
        self.gui_manager.update(GlobalPygame.delta_time)
        self.gui_manager.draw_ui(GlobalPygame.window)

        # Handle button click
        if self.join_button.check_pressed():
            self.join()

    def join(self):
        Logger.log("Joining game")
        username = self.text_inputs["username"].text
        # server_ip = self.text_inputs["server"].text
        # TESTING XXX
        server_ip = "127.0.0.1:6500"

        if not check_username(username):
            Logger.fatal("Invalid username!")
            self.display_dialog(
                identifier="invalid_username",
                message="Invalid username!",
                text_size=32,
                center=True,
            )
            return

        try:
            ip, port = hisock.utils.ipstr_to_tup(server_ip)
            hisock.utils.validate_ipv4((ip, port), require_port=True)
        except ValueError:
            Logger.fatal("Invalid IP!")
            self.display_dialog(
                identifier="invalid_ip",
                message="Invalid IP address!",
                text_size=32,
                center=True,
            )
            return

        Logger.log(f"Connecting: {username}@{ip} on port {port}")

        try:
            client = hisock.client.ThreadedHiSockClient(
                (ip, port), name=username, group=None
            )
            # New state
            update_state(GameState, client)
        except Exception as e:
            self.display_dialog(
                identifier="connect_error",
                message=f"An error whilst connecting has occurred!\n{Logger.log_error(e)}",
                text_size=12,
                center=False,
            )
