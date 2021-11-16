"""
Snake, but multiplayer
Created by sheepy0125
16/11/2021

Shared game code
"""

### Setup ###
from tools import Logger
from config_parser import parse

CONFIG: dict = parse()

### Classes ###
class SharedGame:
    """
    Dataclass for game information
    Must be the same between the client and the server!
    """

    window_width: int = 800
    window_height: int = 600
    height: int = window_width // 10
    width: int = window_height // 10


class BaseSnakePlayer:
    """
    Since each the server and the client will have a snake player, we will
    use inheritence from this class to make the code specific to what end
    this is on.
    The inherited class must have a method called `snake_died` which will
    deal with whatever needs to happen when the snake dies.
    """

    def __init__(
        self,
        default_pos: tuple,
        default_length: int = 1,
        identifier: int | str = "unknown snake",
    ):
        self.identifier = identifier
        self.pos = default_pos
        self.tail: list[tuple] = [default_pos]  # List of positions
        self.tail_length = default_length
        self.alive = True

        self.direction = "right"
        self.direction_velocity_enum = {
            "up": (0, -1),
            "down": (0, 1),
            "left": (-1, 0),
            "right": (1, 0),
        }

        if CONFIG["verbose"]:
            Logger.log(f"Snake {self.identifier} created")

    def move(self):
        ...

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
        Logger.warn(
            "This shouldn't be called!! Read the docstring for BaseSnakePlayer for why"
        )
        Logger.info(f"Snake {self.identifier} died because {reason = }")
