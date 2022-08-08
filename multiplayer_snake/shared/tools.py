"""
Snake, but multiplayer
Created by sheepy0125
2021-10-02

Tools
"""

# pylint: disable=unused-import

### Setup ###
import os  # Platform checking for ANSI colors
from time import strftime
from urllib import request
from random import randint
from traceback import format_exc
from multiplayer_snake.constants import DISALLOWED_CHARS_FOR_USERNAME

### Logger ###
class Logger:
    """Log messages with ease"""

    colors: dict = {
        "log": "\033[92m",
        "warn": "\033[93m",
        "fatal": "\033[91m",
        "normal": "\033[0m",
    }

    # If the user isn't on POSIX, allow colors
    if os.name != "posix":
        os.system("color")

    @staticmethod
    def time() -> str:
        """Format current time"""
        return f"{strftime('[%b/%d/%y %I:%M:%S %p]')}"

    @staticmethod
    def log(message: str):
        print(
            f"{Logger.time()} {Logger.colors['log']}[INFO] {message!s}"
            f"{Logger.colors['normal']}"
        )

    @staticmethod
    def verbose(message: str, check: bool = True):
        if check:
            from multiplayer_snake.shared.config_parser import parse

            if not parse()["verbose"]:
                return

        print(
            f"{Logger.time()} {Logger.colors['warn']}[VERB]{Logger.colors['normal']} "
            f"{message!s}"
        )

    @staticmethod
    def warn(message: str):
        print(
            f"{Logger.time()} {Logger.colors['warn']}[WARN] {message!s}"
            f"{Logger.colors['normal']}"
        )

    @staticmethod
    def fatal(message: str):
        print(
            f"{Logger.time()} {Logger.colors['fatal']}[FAIL] {message!s}"
            f"{Logger.colors['normal']}"
        )

    @staticmethod
    def log_error(error: Exception) -> str:
        error_message = (
            f"{type(error).__name__}: {str(error)} (line {error.__traceback__.tb_lineno})"
            f"\n{format_exc()}\n...\n"
        )
        Logger.fatal(error_message)
        return error_message


### Get public IP ###
def get_public_ip() -> str:
    """Get the public IP address"""

    from multiplayer_snake.shared.config_parser import parse

    if not parse()["show_public_ip"]:
        return "0.0.0.0"

    try:
        req = request.Request("https://icanhazip.com/")
        with request.urlopen(req) as response:
            return response.read().decode("ascii")[:-1]  # Remove newline
    except Exception as error:
        Logger.fatal(f"Failed to get public IP: {error}")
        return "0.0.0.0"


### Get discriminator ###
def get_discriminator(size: int = 4) -> str:
    """Returns a discriminator of size length"""

    return "".join([f"{randint(0, 9)!s}" for _ in range(size)])


### Check username ###
def check_username(username: str) -> bool:
    """Checks if username is valid"""

    return (
        len(username) >= 3
        and len(username) <= 16
        and username.isidentifier()
        and not any(char in DISALLOWED_CHARS_FOR_USERNAME for char in username)
    )
