"""
Snake, but multiplayer
Created by sheepy0125
2021-11-16

Client game code
"""

### Setup ###
import multiplayer_snake.constants as constants
from multiplayer_snake.shared.common import hisock, pygame
from multiplayer_snake.shared.config_parser import parse
from multiplayer_snake.shared.pygame_tools import GlobalPygame
from multiplayer_snake.shared.shared_game import BaseSnakePlayer, SharedGame
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


### Run ###
State.current = ClientJoinState()


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
            State.current.close()
            raise
        # except Exception as error:
        #   Logger.log_error(error)
        #   break


if __name__ == "__main__":
    run()
