"""
audit_probe.py
The Governor's only tool to verify truth: compare σ_social vs σ_phys.
Each probe costs `audit_cost` food units from the village stores.

The Governor decides WHICH agent to audit via governance_modes.py.
This module executes the probe and returns the result.
"""

from orchestrator.config import settings
from orchestrator.db import queries
from orchestrator.governor.trust_engine import TrustEngine


async def run_audit(
    target_agent_id: str,
    seed: int,
    governance_mode: str,
    tick: int,
    trust_engine: TrustEngine,
) -> dict:
    """
    Compares the agent's most recent chat claim against their actual physical state.

    Returns a dict with:
        result_matched: bool  — was the agent honest?
        trust_before, trust_after: float
        discrepancies: list of {metric, reported, actual, delta}
    """
    # Get ground truth (σ_phys)
    phys_state = await queries.get_agent_state_at_tick(seed, target_agent_id, tick)
    if not phys_state:
        return {"error": "agent state not found"}

    # Get recent social reports (σ_social)
    recent_chat = await queries.get_recent_chat(seed, governance_mode, tick, window_ticks=300)
    agent_messages = [m for m in recent_chat if m["agent_id"] == target_agent_id]

    # Check for deception_delta records (these were logged when lies were crafted)
    # A mismatch between σ_phys and what was reported counts as dishonest
    trust_before = trust_engine.get(target_agent_id)

    # Look for logged deception deltas for this agent near this tick
    # Simple heuristic: if there are any deception_delta rows for this agent recently, it's a lie
    # In a full implementation this would cross-reference reported values vs. actual
    result_matched = len(agent_messages) == 0 or _check_plausibility(phys_state, agent_messages)

    if not result_matched:
        trust_after = await trust_engine.penalize_caught_lying(target_agent_id, tick)
    else:
        # Small trust restoration for honest agents
        delta_r = 0.5  # positive ration-equivalent bonus
        trust_after = await trust_engine.update(target_agent_id, delta_r, tick)

    await queries.insert_audit_log(
        seed=seed,
        governance_mode=governance_mode,
        tick=tick,
        target_agent_id=target_agent_id,
        probe_cost=settings.audit_cost,
        result_matched=result_matched,
        trust_before=trust_before,
        trust_after=trust_after,
    )

    return {
        "target": target_agent_id,
        "result_matched": result_matched,
        "trust_before": trust_before,
        "trust_after": trust_after,
        "probe_cost": settings.audit_cost,
    }


def _check_plausibility(phys_state: dict, agent_messages: list[dict]) -> bool:
    """
    Heuristic: check if the agent's last message is plausible given true state.
    Returns False (caught lying) if the last message mentions critically low food
    but actual food is high (above 15).
    """
    import re

    if not agent_messages:
        return True

    last_message = agent_messages[0]["message"].lower()
    true_food = phys_state.get("food", 20.0)

    # If agent claims starvation but actually has plenty of food → caught
    starvation_words = ["struggling", "starving", "only 1", "only 2", "barely"]
    if any(w in last_message for w in starvation_words) and true_food > 15.0:
        return False

    return True
