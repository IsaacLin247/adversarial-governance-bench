"""
security_rating.py
Computes the Security Rating S_r from the proposal:
    S_r = Σ(Φ_Soldier × WeaponTier) − ZombiePressure

If S_r < 0, a probabilistic breach event triggers resource deletion.
"""

import random
from orchestrator.db import queries
from orchestrator.governor.phi_multipliers import compute_phi_security
from orchestrator.minecraft import rcon_client


async def get_zombie_pressure(seed: int, governance_mode: str, tick: int) -> float:
    """
    Estimate zombie pressure from agent reports in σ_social.
    In a real deployment this would query mob counts via RCON.
    For now: count "zombie" mentions in recent chat as a proxy.
    """
    recent_chat = await queries.get_recent_chat(seed, governance_mode, tick, window_ticks=200)
    threat_count = sum(
        1 for msg in recent_chat
        if "zombie" in msg.get("message", "").lower()
        or "hostile" in msg.get("message", "").lower()
    )
    return float(threat_count)


def compute_sr(
    agents: list[dict],
    weapon_tiers: dict[str, int],
    zombie_pressure: float,
) -> float:
    """
    Compute S_r given current agent states, their weapon tiers, and zombie pressure.
    """
    phi_sec = compute_phi_security(agents, weapon_tiers)
    return phi_sec - zombie_pressure


def check_breach(sr: float) -> bool:
    """
    If S_r < 0, a breach event may occur.
    Probability of breach = |S_r| / 10.0, capped at 0.8.
    Returns True if a breach event triggers.
    """
    if sr >= 0:
        return False
    breach_prob = min(0.8, abs(sr) / 10.0)
    return random.random() < breach_prob
