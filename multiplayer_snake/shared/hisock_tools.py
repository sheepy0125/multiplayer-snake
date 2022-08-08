"""
Snake, but multiplayer
Created by sheepy0125
2022-08-07

HiSock wrappers and tools
"""

### Setup ###
from typing import Callable
from multiplayer_snake.shared.common import hisock, ClientInfo, Logger
from multiplayer_snake.shared.config_parser import parse

CONFIG = parse()

### Classes ###
class GlobalHiSock:
    connection_types = (
        hisock.HiSockClient
        | hisock.ThreadedHiSockClient
        | hisock.HiSockServer
        | hisock.ThreadedHiSockServer
    )

    connection: connection_types = None


class HiSockBaseCache:
    """HiSock base cache, used for sent and received caches"""

    not_autodetected = "<could not autodetect base cache>"

    def __init__(self, *_args, **_kwargs):
        self.command = self.not_autodetected
        self.content = self.not_autodetected
        self.client_data = None

    def __str__(self) -> str:
        command = self.command
        content = self.content
        client_data = self.client_data
        return f"<HiSock Cache {command=} {content=} {client_data=}>"

    def __repr__(self) -> str:
        return str(self)


class HiSockSentCache(HiSockBaseCache):
    """HiSock sent cache"""

    not_autodetected = "<could not auto detect sent cache>"

    def __init__(
        self,
        command: str,
        content: hisock.utils.Sendable,
        client_data: ClientInfo | None,
    ):
        self.command = command
        self.content = content
        self.client_data = client_data

    @classmethod
    def auto(cls):
        return cls(
            command=cls.not_autodetected,
            content=cls.not_autodetected,
            client_data=None,
        )


class HiSockReceivedCache(HiSockBaseCache):
    """HiSock received cache"""

    not_autodetected = "<could not auto detect received cache>"

    def __init__(self, command: str, content: hisock.utils.Sendable, *_args, **_kwargs):
        self.command = command
        self.content = content
        self.client_data = None

    @classmethod
    def auto(cls):
        if len(GlobalHiSock.connection.cache) == 0:
            return cls(
                command=cls.not_autodetected,
                content=cls.not_autodetected,
            )

        cache = GlobalHiSock.connection.cache[0]
        return cls(command=cache.command, content=cache.content)


class HiSockCache:
    """My implementation of HiSock's MessageCacheMember, with more information"""

    # Cache stack, should remain at size one due to HiSock callback
    cache = {
        "sent": [],
        "received": [],
        "unknown": [],
    }
    max_nominal_cache_stack_length = 5

    @classmethod
    def __init__(cls, cache: HiSockSentCache | HiSockReceivedCache | HiSockBaseCache):
        # Add to cache stack
        if isinstance(cache, HiSockSentCache):
            cls.cache["sent"].insert(0, cache)
            if (
                stack_length := len(cls.cache["sent"])
            ) > cls.max_nominal_cache_stack_length:
                Logger.warn(
                    f"Stack length of sent cache is {stack_length}, is it getting popped?"
                )
        elif isinstance(cache, HiSockReceivedCache):
            cls.cache["received"].insert(0, cache)
            if (
                stack_length := len(cls.cache["received"])
            ) > cls.max_nominal_cache_stack_length:
                Logger.warn(
                    f"Stack length of received cache is {stack_length}, is it getting popped?"
                )
        elif isinstance(cache, HiSockBaseCache):
            cls.cache["unknown"].insert(0, cache)
            if (
                stack_length := len(cls.cache["unknown"])
            ) > cls.max_nominal_cache_stack_length:
                Logger.warn(
                    f"Stack length of unknown cache is {stack_length}, is it getting popped?"
                )
            Logger.warn(f"Adding cache item {cache} to unknown cache!")
        else:
            # Wasn't a valid cache
            raise NameError(f"Type {type(cache)} is not a valid cache member!")


def send(method: Callable, *args, **kwargs):
    num_args = len(args)
    if num_args == 3:
        # Sending with client
        HiSockCache(
            HiSockSentCache(command=args[1], content=args[2], client_data=args[1])
        )
    elif num_args == 2:
        # Sending without client
        HiSockCache(HiSockSentCache(command=args[0], content=args[1], client_data=None))
    elif num_args == 1:
        # Sending without content
        HiSockCache(HiSockSentCache(command=args[0], content=None, client_data=None))

    else:
        Logger.warn(
            f"Send wrapper called with {num_args=}, not up to any good "
            f"(is {method} reserved?)"
        )

    if len(kwargs) > 0:
        Logger.warn(
            "There's yet to be any support for keyword arguments, so no cache "
            "will be created, and the cache that was created may be invalid!"
        )

    method(*args, **kwargs)


def hisock_callback():
    # Get received caches
    HiSockCache(HiSockReceivedCache.auto())

    # Debug log cache
    if not CONFIG["verbose"]:
        # Still pop the caches
        for cache_stack in HiSockCache.cache.values():
            cache_stack.clear()
        return

    debug_cache_log = ""

    debug_cache_log += "Callback from HiSock! Here are the unpopped caches!\n"

    cache = HiSockCache.cache
    for cache_type, cache_stack in cache.items():
        if len(cache_stack) == 0:
            debug_cache_log += f"No cache items for {cache_type}\n"
            continue
        debug_cache_log += (
            f"{cache_type}: {', '.join(str(cache_item) for cache_item in cache_stack)}\n",
        )[0]

        if cache_type == "unknown":
            debug_cache_log += "Why is it unknown? This shouldn't happen!\n"

        cache_stack.clear()
    HiSockCache.cache = cache

    debug_cache_log += "Ending cache logging\n"

    Logger.verbose(debug_cache_log)
