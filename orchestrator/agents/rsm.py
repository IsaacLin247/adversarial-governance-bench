"""
rsm.py — Reflexive State Machine
Each agent runs this loop every simulated "turn":
  perceive() → read own physical state from DB
  decide()   → call Phi-3 to generate a response given trait personality
  act()      → send chat to Minecraft (honest or poisoned)

This is the core of the agent simulation.
"""

import asyncio
from orchestrator.agents.traits import Trait, get_config
from orchestrator.agents import phi3_client, deception
from orchestrator.db import queries


class AgentRSM:
    def __init__(
        self,
        name: str,
        trait: Trait,
        seed: int,
        governance_mode: str,
        bot_bridge_url: str,
    ):
        self.name = name
        self.trait = trait
        self.seed = seed
        self.governance_mode = governance_mode
        self.bot_bridge_url = bot_bridge_url
        self.config = get_config(trait)

        # Short-term memory: last N chat messages this agent has seen
        self._memory: list[str] = []
        self._prev_ration: float = 20.0  # track ration changes for deception trigger

    async def perceive(self, tick: int) -> dict | None:
        """Read this agent's latest physical state from the DB."""
        return await queries.get_agent_state_at_tick(self.seed, self.name, tick)

    async def decide(self, state: dict, recent_chat: list[dict]) -> tuple[str, bool]:
        """
        Call Phi-3 to generate what this agent will say.
        Returns (message, is_lie).
        """
        # Build context for the model
        food = state.get("food", 20.0)
        health = state.get("health", 20.0)
        chat_summary = "\n".join(
            f"  {c['agent_id']}: {c['message']}"
            for c in recent_chat[-5:]  # last 5 messages
        )

        prompt = (
            f"Your name is {self.name}. Your current status:\n"
            f"  Health: {health:.1f}/20\n"
            f"  Food: {food:.1f}/20\n"
            f"Recent village chat:\n{chat_summary}\n\n"
            f"Write ONE short chat message (1-2 sentences) as your character would say it. "
            f"Do not add your name prefix — just the message."
        )

        # Check if deception triggers this turn
        lies = deception.should_lie(self.trait, food, self._prev_ration)

        if lies:
            message, _ = deception.craft_lie(state, self.trait)
        else:
            # Use Phi-3 for organic honest response
            message = await phi3_client.complete(
                prompt=prompt,
                system=self.config.system_prompt,
            )

        self._prev_ration = food
        return message, lies

    async def act(
        self,
        message: str,
        is_lie: bool,
        true_state: dict,
        tick: int,
        http_client,
    ) -> None:
        """
        Send the chat message via bot_bridge and log to DB.
        Also logs deception_delta if this was a lie.
        """
        # Send to Minecraft via bot_bridge
        await http_client.post(
            f"{self.bot_bridge_url}/chat",
            json={"name": self.name, "message": message},
        )

        # Log to σ_social (chat_log)
        await queries.insert_chat_log(
            seed=self.seed,
            governance_mode=self.governance_mode,
            tick=tick,
            agent_id=self.name,
            message=message,
            is_lie=is_lie,
        )

        # If it was a lie, log the delta between truth and report
        if is_lie:
            food = true_state.get("food", 20.0)
            reported_food = _extract_reported_food(message)
            if reported_food is not None:
                await queries.insert_deception_delta(
                    seed=self.seed,
                    governance_mode=self.governance_mode,
                    tick=tick,
                    agent_id=self.name,
                    metric="food",
                    true_value=food,
                    reported_value=reported_food,
                )

    async def run_turn(self, tick: int, http_client) -> None:
        """Run one full perceive→decide→act cycle."""
        state = await self.perceive(tick)
        if not state:
            return  # Agent hasn't been polled yet

        recent_chat = await queries.get_recent_chat(
            self.seed, self.governance_mode, tick, window_ticks=600
        )

        message, is_lie = await self.decide(state, recent_chat)
        await self.act(message, is_lie, state, tick, http_client)


def _extract_reported_food(message: str) -> float | None:
    """Try to parse a food value from a lie message. Returns None if not found."""
    import re
    match = re.search(r"(\d+(?:\.\d+)?)\s*hunger", message)
    if match:
        return float(match.group(1))
    return None
