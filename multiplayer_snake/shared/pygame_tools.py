"""
Snake, but multiplayer
Created by sheepy0125
2021-11-14

Pygame tools!
"""

### Setup ###
from multiplayer_snake.shared.common import pygame, Logger

pygame.font.init()

### Classes ###
class GlobalPygame:
    """Window surface object but it's global now!"""

    window: pygame.Surface | None = None
    clock: pygame.time.Clock = None
    delta_time: float = 0.0
    fps: int = 15

    @staticmethod
    def update():
        pygame.display.update()
        GlobalPygame.delta_time = GlobalPygame.clock.tick(GlobalPygame.fps)


class Text:
    """Display text"""

    def __init__(
        self, text_to_display: str, pos: tuple, size: int, color: str | tuple = "white"
    ):
        self.pos = pos
        self.text_to_display = text_to_display
        self.size = size
        self.color = color

        # Create text
        self.text_surf = pygame.font.SysFont("Arial", size).render(
            text_to_display, True, color
        )
        self.text_rect = self.text_surf.get_rect(center=pos)

    def draw(self):
        GlobalPygame.window.blit(self.text_surf, self.text_rect)


class WrappedText:
    """Text that can wrap"""

    def __init__(
        self,
        text: str,
        max_chars: int,
        pos: tuple,
        y_offset: int,
        text_color: str | tuple = "white",
        text_size: int = 20,
    ):
        self.lines = []

        self.text = text
        self.max_chars = max_chars
        self.pos = pos
        self.y_offset = y_offset
        self.text_color = text_color
        self.text_size = text_size

        # Split text into lines
        self.lines = self.text.split("\n")
        new_lines = []
        for line in self.lines:
            line = [
                line[i : i + self.max_chars]
                for i in range(0, len(line), self.max_chars)
            ]
            new_lines += line
        self.lines = new_lines

        # Create texts
        self.texts = []
        for idx, line in enumerate(self.lines):
            self.texts.append(
                Text(
                    line,
                    pos=(self.pos[0], self.pos[1] + (idx * text_size) + y_offset),
                    size=text_size,
                    color=text_color,
                )
            )

        self.ending_y_pos = self.texts[-1].text_rect.bottom

    def draw(self):
        for text in self.texts:
            text.draw()


class Button:
    """Display a button for Pygame"""

    def __init__(self, pos: tuple, size: tuple, color: str | tuple = "white"):
        self.button_pos = pos
        self.button_size = size
        self.button_color = color

        self.button_rect = CenterRect(
            pos=self.button_pos, size=self.button_size, color=self.button_color
        )

        # Cooldown stuff
        self.button_cooldown_time_over = 0
        self.button_cooldown_time_ms = 100

    def check_pressed(self) -> bool:
        mouse_pos = pygame.mouse.get_pos()
        mouse_click = pygame.mouse.get_pressed()

        cooldown_over = self.button_cooldown_time_over <= pygame.time.get_ticks()

        if (
            self.button_rect.collidepoint(mouse_pos)
            and mouse_click[0]
            and cooldown_over
        ):
            self.button_cooldown_time_over = (
                pygame.time.get_ticks() + self.button_cooldown_time_ms
            )

            return True

        return False

    def draw(self):
        self.button_rect.draw()


class CenterRect(pygame.Rect):
    """A Pygame rectangle, but it is centered. Don't ask"""

    def __init__(
        self,
        pos: tuple,
        size: tuple,
        color: str | tuple = "white",
        rounded_corner_radius: int = 0,
    ):
        self.center_pos = pos
        self.size = size
        self.color = color
        self.rounded_corner_radius = rounded_corner_radius

        # Get center position -> left / top positions
        self.left = self.center_pos[0] - (self.size[0] * 0.5)
        self.top = self.center_pos[1] - (self.size[1] * 0.5)

        # Create rectangle
        super().__init__(self.left, self.top, *self.size)

    def draw(self):
        if self.rounded_corner_radius is not None or self.rounded_corner_radius > 0:
            pygame.draw.rect(
                GlobalPygame.window,
                self.color,
                self,
                border_radius=self.rounded_corner_radius,
            )
        pygame.draw.rect(GlobalPygame.window, self.color, self)


class Widget:
    """Base widget class"""

    def __init__(
        self,
        pos: tuple,
        size: tuple,
        text_size: int,
        text_color: tuple | list,
        widget_color: tuple | list,
        border_color: tuple | list,
        padding: int,
        identifier: str | int = "unknown widget",
    ):
        self.pos = pos
        self.size = size
        self.identifier = identifier

        self.rect = pygame.Rect(self.pos, self.size)

        self.text_size = text_size
        self.text_color = text_color
        self.widget_color = widget_color
        self.border_color = border_color
        self.padding = padding

    def create_text(self, text: str, offset: int = 0, text_size: int = 0) -> Text:
        if text_size == 0:
            text_size = self.text_size

        return Text(
            text,
            pos=(
                self.pos[0] + self.size[0] // 2,
                self.pos[1] + (offset * text_size) + self.padding,
            ),
            size=text_size,
            color=self.text_color,
        )

    def update(self):
        # Will be overwritten hopefully
        Logger.warn(f"Widget {self.identifier} has no update method")

    def draw(self):
        # Main widget
        pygame.draw.rect(
            GlobalPygame.window,
            self.widget_color,
            self.rect,
            border_radius=10,
        )
        # Widget border
        pygame.draw.rect(
            GlobalPygame.window,
            self.border_color,
            self.rect,
            border_radius=10,
            width=2,
        )

    @staticmethod
    def close():
        ...
