"""
state_poller.py
Polls the bot_bridge every poll_interval_ticks and writes σ_phys to PostgreSQL.
This is the ground-truth data pipeline — it cannot be lied about by agents.
"""

import asyncio
import httpx
from orchestrator.config import settings
from orchestrator.db import queries


class StatePoller:
    def __init__(self, seed: int, governance_mode: str):
        self.seed = seed
        self.governance_mode = governance_mode
        self.tick = 0
        self._running = False

    async def poll_once(self) -> list[dict]:
        """Fetch all bot states from bot_bridge and write to DB. Returns states."""
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{settings.bot_bridge_url}/state")
            resp.raise_for_status()
            all_states = resp.json()

        for name, state in all_states.items():
            if not state.get("online"):
                continue
            await queries.insert_agent_state(
                seed=self.seed,
                governance_mode=self.governance_mode,
                tick=self.tick,
                agent_id=name,
                health=state["health"],
                food=state["food"],
                x=state["x"],
                y=state["y"],
                z=state["z"],
                inventory=state["inventory"],
                role=state["role"],
                is_alive=state["health"] > 0,
            )

        return list(all_states.values())

    async def run(self) -> None:
        """Continuously poll at poll_interval_ticks rate until stopped."""
        self._running = True
        # At 20 ticks/second real time, poll_interval_ticks=20 → 1 poll/second
        interval_seconds = settings.poll_interval_ticks / 20.0

        while self._running:
            try:
                await self.poll_once()
            except Exception as e:
                print(f"[state_poller] tick {self.tick} poll error: {e}")
            self.tick += settings.poll_interval_ticks
            await asyncio.sleep(interval_seconds)

    def stop(self) -> None:
        self._running = False
