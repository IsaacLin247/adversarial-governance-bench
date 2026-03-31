"""
trust_engine.py
Implements the Trust Hysteresis formula from the proposal:
    T_{t+1} = T_t - α(ΔR)

Where:
  - ΔR = ration change (positive = more food, negative = less food)
  - α = trust_alpha_base (3× higher for losses than gains, per proposal)

Trust scores are kept in memory for fast reads during simulation.
Every update is also persisted to trust_history in PostgreSQL.
"""

import asyncio
from orchestrator.config import settings
from orchestrator.db import queries


class TrustEngine:
    def __init__(self, seed: int, governance_mode: str):
        self.seed = seed
        self.governance_mode = governance_mode
        # Trust scores keyed by agent_id, initialized at 1.0 (full trust)
        self._scores: dict[str, float] = {}

    def get(self, agent_id: str) -> float:
        return self._scores.get(agent_id, 1.0)

    def get_all(self) -> dict[str, float]:
        return dict(self._scores)

    def get_average(self) -> float:
        if not self._scores:
            return 1.0
        return sum(self._scores.values()) / len(self._scores)

    async def update(self, agent_id: str, delta_r: float, tick: int) -> float:
        """
        Apply the trust hysteresis formula and persist to DB.

        Args:
            delta_r: The ration change (positive = increase, negative = decrease)
            tick: Current simulation tick

        Returns:
            New trust score for this agent
        """
        current = self.get(agent_id)
        alpha = settings.trust_alpha_base

        # Loss events are 3× more damaging to trust than gains
        if delta_r < 0:
            alpha *= settings.trust_loss_multiplier

        new_score = current - alpha * delta_r
        # Clamp to [0.0, 1.0]
        new_score = max(0.0, min(1.0, new_score))
        self._scores[agent_id] = new_score

        await queries.insert_trust_history(
            seed=self.seed,
            governance_mode=self.governance_mode,
            tick=tick,
            agent_id=agent_id,
            trust_score=new_score,
            delta_r=delta_r,
        )

        return new_score

    async def penalize_caught_lying(self, agent_id: str, tick: int) -> float:
        """Apply a large trust penalty when an audit catches an agent lying."""
        # A caught lie is treated as a severe ration cut (delta_r = -5.0)
        return await self.update(agent_id, delta_r=-5.0, tick=tick)

    async def restore_from_db(self) -> None:
        """On restart, reload the latest trust scores from the database."""
        scores = await queries.get_latest_trust_scores(self.seed, self.governance_mode)
        self._scores.update(scores)
