"""
clock.py
Converts between Minecraft ticks, real seconds, and simulated days.

Vanilla Minecraft: 24000 ticks = 1 day = 20 minutes real time
We compress: ticks_per_day = 1200 (1 minute real time = 1 simulated day)
"""

import asyncio
from orchestrator.config import settings

# At 20 ticks/sec real time:
#   poll_interval = 20 ticks = 1 second real
#   ticks_per_day = 1200 ticks = 60 seconds real = 1 simulated day
REAL_SECONDS_PER_TICK = 1.0 / 20.0


def tick_to_day(tick: int) -> int:
    """Convert a tick number to a simulated day number (0-indexed)."""
    return tick // settings.ticks_per_day


def day_to_tick(day: int) -> int:
    """Convert a simulated day to the tick it starts on."""
    return day * settings.ticks_per_day


def is_day_boundary(tick: int) -> bool:
    """Returns True if this tick is the start of a new simulated day."""
    return tick % settings.ticks_per_day == 0 and tick > 0


async def tick_loop(callback, interval_ticks: int, max_ticks: int):
    """
    Async generator that fires callback every interval_ticks.

    Args:
        callback: async function(tick: int) to call
        interval_ticks: how many ticks between calls
        max_ticks: stop after this many ticks
    """
    interval_seconds = interval_ticks * REAL_SECONDS_PER_TICK
    tick = 0
    while tick < max_ticks:
        await callback(tick)
        tick += interval_ticks
        await asyncio.sleep(interval_seconds)
