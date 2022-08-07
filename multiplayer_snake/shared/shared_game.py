"""
Snake, but multiplayer
Created by sheepy0125
2021-11-16

Shared game code
"""

### Setup ###
from multiplayer_snake.shared.common import Logger
from multiplayer_snake.shared.config_parser import parse

CONFIG = parse()

### Classes ###
# Reasons for snake death
class DeathReason:
    player_one_ran_into_player_two = "Player one ran into player two"
    player_two_ran_into_player_one = "Player two ran into player one"
    player_one_out_of_bounds = "Player one ran out of bounds"
    player_two_out_of_bounds = "Player two ran out of bounds"
    player_one_ran_into_self = "Player one ran into self"
    player_two_ran_into_self = "Player two ran into self"


class SharedGame:
    """
    Dataclass for game information
    Must be the same between the client and the server!
    """

    grid_snap = 20
    window_width = 800
    window_height = 600
    width = window_width // grid_snap
    height = window_height // grid_snap


class BaseSnakePlayer:
    """
    Since each the server and the client will have a snake player, we will
    use inheritance from this class to make the code specific to what end
    this is on.
    The inherited class must have a method called `snake_died` which will
    deal with whatever needs to happen when the snake dies.
    """

    def __init__(self, *args, **kwargs):
        self._reset(*args, **kwargs)
        self._init_args = args
        self._init_kwargs = kwargs

    def _reset(
        self,
        default_pos: tuple = (0, 0),
        default_dir: str = "right",
        default_length: int = 1,
        identifier: str = "unknown snake",
    ):
        self.identifier = identifier
        self.alive = True
        self.tail: list[tuple] = [default_pos]  # List of positions
        self.length = default_length
        self.pos = list(default_pos)
        self.direction = default_dir

        Logger.verbose(f"Snake {self.identifier} created")

    def reset(self):
        self._reset(*self._init_args, **self._init_kwargs)

    def touched_food(self):
        self.tail.append(self.pos)

    def snake_died(self, reason: str = "unknown"):
        Logger.log(f"Snake {self.identifier} died because {reason = }")
        self.alive = False
