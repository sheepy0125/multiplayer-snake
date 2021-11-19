"""
Tools for Some Platformer Game
Created by sheepy0125
02/10/2021
"""

### Setup ###
import os  # Platform checking for ANSI colors
from time import strftime
from urllib import request

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
        del os

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
    def log_error(error: Exception):
        Logger.fatal(
            f"{type(error).__name__}: {str(error)} (line {error.__traceback__.tb_lineno})"
        )


### Get public IP ###
def get_public_ip() -> str:
    """Get the public IP address"""

    try:
        req = request.Request("https://icanhazip.com/")
        with request.urlopen(req) as response:
            return response.read().decode("ascii")[:-1]  # Remove newline
    except Exception as error:
        Logger.fatal(f"Failed to get public IP: {error}")
        return "0.0.0.0"
