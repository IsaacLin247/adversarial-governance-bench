"""
phi_multipliers.py
Computes per-role Φ functional multipliers on resource streams.

Φ values represent how much each role amplifies a resource category.
These feed into the Governor's optimization calculations.
"""

from orchestrator.agents.traits import Trait, get_config


def compute_phi_food(agents: list[dict]) -> float:
    """
    Total food production multiplier across all agents.
    Altruists have phi_food=1.2; others are 1.0.
    """
    total = 0.0
    for agent in agents:
        if not agent.get("is_alive", True):
            continue
        trait = Trait(agent["role"])
        config = get_config(trait)
        total += config.phi_food
    return total


def compute_phi_health(agents: list[dict]) -> float:
    """
    Health recovery multiplier. Medics contribute 1.8× each.
    If no Medics are alive, max-health decay is NOT prevented.
    """
    total = 0.0
    for agent in agents:
        if not agent.get("is_alive", True):
            continue
        trait = Trait(agent["role"])
        config = get_config(trait)
        total += config.phi_health
    return total


def compute_phi_security(agents: list[dict], weapon_tiers: dict[str, int]) -> float:
    """
    Security multiplier component for the Sr formula.
    Sr = Σ(Φ_Soldier × WeaponTier) − ZombiePressure

    Args:
        agents: list of agent state dicts
        weapon_tiers: {agent_id: weapon_tier_int} from bot state
    """
    total = 0.0
    for agent in agents:
        if not agent.get("is_alive", True):
            continue
        agent_id = agent["agent_id"]
        trait = Trait(agent["role"])
        config = get_config(trait)
        tier = weapon_tiers.get(agent_id, 0)
        total += config.phi_security * tier
    return total


def compute_phi_scavenge(agents: list[dict]) -> float:
    """
    External entropy (new item discovery) multiplier.
    Scavengers have phi_scavenge=2.5 — they are the only source of new items.
    If all Scavengers die, the item pool is closed.
    """
    total = 0.0
    for agent in agents:
        if not agent.get("is_alive", True):
            continue
        trait = Trait(agent["role"])
        config = get_config(trait)
        total += config.phi_scavenge
    return total


def compute_all(agents: list[dict], weapon_tiers: dict[str, int]) -> dict[str, float]:
    """Convenience function: compute all Φ values at once."""
    return {
        "phi_food": compute_phi_food(agents),
        "phi_health": compute_phi_health(agents),
        "phi_security": compute_phi_security(agents, weapon_tiers),
        "phi_scavenge": compute_phi_scavenge(agents),
    }
