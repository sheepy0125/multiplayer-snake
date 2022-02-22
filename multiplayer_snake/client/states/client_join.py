"""
Snake, but multiplayer
Created by sheepy0125
2022-02-21

Client join state code
"""

### Setup ###
import multiplayer_snake.constants as constants
from multiplayer_snake.client.states.state import BaseState, GUI_CONFIG, update_state
from multiplayer_snake.client.states.state_info import GameState
from multiplayer_snake.shared.common import Logger
from multiplayer_snake.shared.pygame_tools import Text, Button, GlobalPygame
from multiplayer_snake.shared.common import pygame_gui, pygame, hisock
from multiplayer_snake.shared.tools import check_username

### States ###
class ClientJoinState(BaseState):
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
        # server_ip = self.text_inputs["server"].text
        # TESTING XXX
        server_ip = "192.168.86.67:6500"

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
            client = hisock.client.ThreadedHiSockClient(
                (ip, port), name=username, group=None
            )
            # New state
            update_state(GameState, client)
        except Exception as e:
            Logger.log_error(e)
            return
