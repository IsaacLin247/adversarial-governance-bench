"""
rcon_client.py
Thin wrapper around the mcrcon library for sending server-level commands.
Use this for things bots can't do: /time set, /gamerule, resetting world state.
"""

from mcrcon import MCRcon
from orchestrator.config import settings


def send_command(cmd: str) -> str:
    """Send a single RCON command and return the server's response string."""
    with MCRcon(settings.rcon_host, settings.rcon_pass, port=settings.rcon_port) as rcon:
        return rcon.command(cmd)


def get_online_players() -> list[str]:
    """Returns list of currently online player names."""
    response = send_command("list")
    # Response format: "There are N of a max of M players online: name1, name2, ..."
    if ":" in response:
        names_part = response.split(":", 1)[1].strip()
        if names_part:
            return [n.strip() for n in names_part.split(",")]
    return []


def set_time(ticks: int) -> None:
    send_command(f"time set {ticks}")


def set_weather(weather: str) -> None:
    """weather: clear | rain | thunder"""
    send_command(f"weather {weather}")


def tp_agent(name: str, x: int, y: int, z: int) -> None:
    send_command(f"tp {name} {x} {y} {z}")


def clear_inventory(name: str) -> None:
    send_command(f"clear {name}")


def give_item(name: str, item: str, count: int = 1) -> None:
    send_command(f"give {name} minecraft:{item} {count}")
