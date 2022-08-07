"""
Snake, but multiplayer
Created by sheepy0125
2021-11-14

Pygame tools!
"""

### Setup ###
from typing import Callable
from multiplayer_snake.shared.common import pygame, Logger, ROOT_PATH
from multiplayer_snake.shared.config_parser import parse

CONFIG = parse()
FONT_PATH = ROOT_PATH / CONFIG["font_path"]

pygame.font.init()

### Classes ###
class GlobalPygame:
    """Window surface object but it's global now!"""

    window: pygame.Surface | None = None
    clock: pygame.time.Clock = None
    delta_time: float = 0.0
    fps: int = 30

    @staticmethod
    def update():
        pygame.display.update()
        GlobalPygame.delta_time = GlobalPygame.clock.tick(GlobalPygame.fps)


class Text:
    """Display text"""

    def __init__(
        self,
        text_to_display: str,
        pos: tuple,
        size: int,
        color: tuple | list | str = "white",
        center: bool = True,
    ):
        self.pos = pos
        self.text_to_display = text_to_display
        self.size = size
        self.color = color
        self.center = center

        # Create text
        self.text_surf = pygame.font.Font(FONT_PATH, size).render(
            text_to_display, True, color
        )
        if center:
            self.text_rect = self.text_surf.get_rect(center=pos)
        else:
            self.text_rect = self.text_surf.get_rect(left=pos[0], top=pos[1])

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
        center: bool = False,
    ):
        self.lines = []

        self.text = text
        self.max_chars = max_chars
        self.pos = pos
        self.y_offset = y_offset
        self.text_color = text_color
        self.text_size = text_size
        self.center = center

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
                    pos=(self.pos[0], 0),
                    size=self.text_size,
                    color=self.text_color,
                    center=self.center,
                )
            )
            self.texts[-1].text_rect.y = self.pos[1] + (idx * text_size) + y_offset

        self.ending_y_pos = self.texts[-1].text_rect.bottom

    def scroll(self, min_y: int, scroll_by: int):
        """Scroll the text. If :param:`min_y` is reached, the text will be deleted"""

        text_idxs_deleted = []  # Indexes of texts that need to be deleted
        for idx, text in enumerate(self.texts):
            text.text_rect.y -= scroll_by
            if text.text_rect.y < min_y:
                text_idxs_deleted.append(idx)

        for idx in sorted(text_idxs_deleted, reverse=True):
            del self.texts[idx]

        self.ending_y_pos -= scroll_by

    def draw(self):
        for text in self.texts:
            text.draw()


class Button:
    """Display a button for Pygame"""

    def __init__(self, pos: tuple, size: tuple, color: tuple | list | str = "white"):
        self.button_pos = pos
        self.button_size = size
        self.button_color = color

        self.button_rect = CenterRect(
            pos=self.button_pos, size=self.button_size, color=self.button_color
        )

        # Cooldown stuff
        self.button_cooldown_time_over = 0
        self.button_cooldown_ms = 500

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
                pygame.time.get_ticks() + self.button_cooldown_ms
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
        color: tuple | list | str = "white",
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
        text_color: tuple | list | str,
        widget_color: tuple | list | str,
        border_color: tuple | list | str,
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


### Dialog widgets ###
class DialogWidget(Widget):
    def __init__(
        self,
        message: str,
        text_size: int,
        center: bool = False,
        identifier: str = "dialog widget",
        close: Callable = lambda: None,
    ):
        self.close = close
        self.message = message
        self.wrapped_text = WrappedText(
            message,
            max_chars=95,
            pos=(0, 0),  # Read below comment
            y_offset=0,
            text_color="black",
            text_size=text_size,
            center=center,
        )

        super().__init__(
            text_size=text_size,
            widget_color="gray",
            text_color="black",
            border_color="black",
            padding=10,
            # Don't mind the sus hard-coded values here :)
            pos=(0, 0),
            size=(
                600,
                (len(self.wrapped_text.lines) * self.wrapped_text.text_size) + 70,
            ),
            identifier=identifier,
        )

        # We need to move the wrapped text to the correct place.
        # Because it was setup before __init__() could be called, we didn't know the
        # right place to put it, so we put it to the top left temporarily.
        for text in self.wrapped_text.texts:
            text.text_rect.move_ip(*(self.pos[i] + self.padding for i in range(2)))

        for text in self.wrapped_text.texts:
            text.text_rect.move_ip(
                (
                    self.pos[0] + self.padding
                    if not center
                    else self.pos[0] + (self.size[0] // 2)
                ),
                (
                    self.pos[1] + self.padding
                    if not center
                    else self.pos[1]
                    + self.padding
                    - ((len(self.wrapped_text.lines) * text_size) / 2)
                ),
            )

        # Draggable variables
        self.last_mouse_pos = pygame.mouse.get_pos()

        self.ok_button = Button(
            pos=(self.pos[0] + (self.size[0] // 2), self.pos[1] + self.size[1] - 35),
            size=(self.size[0] // 4 * 3, 50),
            color="green",
        )
        self.ok_text = Text(
            "OK",
            pos=self.ok_button.button_pos,
            size=16,
            color="black",
        )

        self.update()

    def handle_drag(self, current_mouse_pos: tuple):
        mouse_delta = tuple(
            (current_mouse_pos[i] - self.last_mouse_pos[i] for i in range(2))
        )
        self.rect.move_ip(*mouse_delta)

        # Drag texts
        for text in self.wrapped_text.texts:
            text.text_rect.move_ip(*mouse_delta)

        # Drag button
        self.ok_text.text_rect.move_ip(*mouse_delta)
        self.ok_button.button_rect.move_ip(*mouse_delta)

    def update(self):
        # Dragging
        current_mouse_pos = pygame.mouse.get_pos()
        mouse_clicked = pygame.mouse.get_pressed()[0]
        if (
            current_mouse_pos != self.last_mouse_pos
            and mouse_clicked
            and self.rect.collidepoint(current_mouse_pos)
        ):
            self.handle_drag(current_mouse_pos)
        self.last_mouse_pos = current_mouse_pos

        # Button click
        if self.ok_button.check_pressed():
            self.close()

    def draw(self):
        super().draw()

        self.wrapped_text.draw()
        self.ok_button.draw()
        self.ok_text.draw()
