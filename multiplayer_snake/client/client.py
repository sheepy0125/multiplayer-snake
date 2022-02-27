"""
Snake, but multiplayer
Created by sheepy0125
2021-11-16

Client game code
"""

### Setup ###
import multiplayer_snake.constants as constants
from multiplayer_snake.shared.common import pygame, Logger
from multiplayer_snake.shared.config_parser import parse
from multiplayer_snake.shared.pygame_tools import GlobalPygame
from multiplayer_snake.client.states.state import State
from multiplayer_snake.client.states.state_info import ClientJoinState

CONFIG = parse()
GUI_CONFIG = CONFIG["gui"]
CLIENT_CONFIG = CONFIG["client"]

# Setup pygame
pygame.init()
GlobalPygame.window = pygame.display.set_mode(GUI_CONFIG["window_size"])
GlobalPygame.clock = pygame.time.Clock()
pygame.display.set_caption(f"{constants.__name__} Client (GUI)")

# Setup state
State.current = ClientJoinState()

### Run ###
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
        except KeyboardInterrupt:
            print("\nExiting gracefully", end="... ")
            State.current.close()
            return
        except Exception as error:
            Logger.log_error(error)
            return


if __name__ == "__main__":
    run()
