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
class SharedGame:
    """
    Dataclass for game information
    Must be the same between the client and the server!
    """

    grid_snap: int = 10
    window_width: int = 800
    window_height: int = 800
    height: int = window_width // grid_snap
    width: int = window_height // grid_snap - 20


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
        default_length: int = 1,
        identifier: int | str = "unknown snake",
    ):
        self.identifier = identifier
        self.alive: bool = True
        self.tail: list[tuple] = [default_pos]  # List of positions
        self.length = default_length
        self.pos = default_pos
        self.direction: str = "right"

        if CONFIG["verbose"]:
            Logger.log(f"Snake {self.identifier} created")

    def reset(self):
        self._reset(*self._init_args, **self._init_kwargs)

    def move(self):
        # Update position
        for dimension in range(2):
            self.pos[dimension] = (
                self.pos[dimension]
                + self.direction_velocity_enum[self.direction][dimension]
            )

        self.tail.insert(0, self.pos)
        self.tail.pop()

    def collision_checking(self, other_snake_object: "BaseSnakePlayer"):
        # Check if the snake is out of bounds
        if (self.pos[0] < 0 or self.pos[0] >= SharedGame.width) or (
            self.pos[1] < 0 or self.pos[1] >= SharedGame.height
        ):
            self.snake_died(reason="out of bounds")

        # Check if the snake is colliding with itself
        for pos in self.tail:
            if pos == self.pos:
                self.snake_died(reason="collided with self")

        # Check if the snake is colliding with the other snake
        for pos in other_snake_object.tail:
            if pos == self.pos:
                self.snake_died(reason="collided with other snake")

    def snake_died(self, reason: str = "unknown"):
        if isinstance(self, BaseSnakePlayer):  # If not derived at all
            Logger.warn(f"Snake {self.identifier} has no snake_died handler!")

        Logger.log(f"Snake {self.identifier} died because {reason = }")
        self.alive = False

        # Typically in a normal snake game, we'd need to reset everything
        # now. But, since this is multiplayer snake, the server will handle
        # that.
