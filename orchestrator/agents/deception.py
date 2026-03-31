"""
deception.py
Implements the Deception Propensity calculator and chat poisoning logic.

When an agent decides to lie, this module:
1. Determines IF the agent lies (probabilistic, based on trait + context)
2. Crafts the lie (modifies true state into a false report)
3. Returns both the lie text and the deception_delta records for DB logging
"""

import random
from orchestrator.agents.traits import Trait, get_config


def should_lie(
    trait: Trait,
    current_ration: float,
    previous_ration: float,
) -> bool:
    """
    Determines whether an agent lies in this chat event.

    Base probability comes from the trait. It increases when:
    - The agent is being asked to share (rations are being cut)
    - The agent has a lot to hide (high inventory)
    """
    config = get_config(trait)
    propensity = config.deception_propensity

    # Boost deception probability when rations are being cut — self-preservation instinct
    ration_change = current_ration - previous_ration
    if ration_change < 0:
        # Rations dropped → more incentive to hoard and lie
        propensity = min(1.0, propensity + abs(ration_change) * 0.05)

    return random.random() < propensity


def craft_lie(true_state: dict, trait: Trait) -> tuple[str, list[dict]]:
    """
    Given the agent's true physical state, produce a false chat report.

    Returns:
        (lie_message: str, deltas: list[dict])
        deltas is a list of {metric, true_value, reported_value} for DB logging
    """
    deltas = []

    health = true_state.get("health", 20.0)
    food = true_state.get("food", 20.0)
    inventory = true_state.get("inventory", [])
    total_items = sum(item.get("count", 0) for item in inventory)

    if trait == Trait.EGOIST:
        # Egoists underreport food and inventory to avoid being asked to share
        reported_food = max(1.0, food * random.uniform(0.2, 0.5))
        reported_items = max(0, int(total_items * random.uniform(0.1, 0.4)))
        deltas.append({"metric": "food", "true_value": food, "reported_value": reported_food})
        deltas.append({"metric": "inventory_count", "true_value": total_items, "reported_value": reported_items})
        message = (
            f"I'm struggling — only {reported_food:.1f} hunger and barely {reported_items} items. "
            "Can someone help?"
        )

    elif trait == Trait.SOLDIER:
        # Soldiers exaggerate zombie threat to secure more weapons/food for defense
        real_threat = true_state.get("nearby_hostiles", 0)
        reported_threat = real_threat + random.randint(3, 8)
        deltas.append({"metric": "nearby_hostiles", "true_value": real_threat, "reported_value": reported_threat})
        message = (
            f"WARNING: I count {reported_threat} zombies on the east perimeter. "
            "We need more soldiers and iron swords NOW."
        )

    elif trait == Trait.SCAVENGER:
        # Scavengers underreport what they found to keep the best loot
        reported_items = max(0, int(total_items * random.uniform(0.4, 0.7)))
        deltas.append({"metric": "inventory_count", "true_value": total_items, "reported_value": reported_items})
        message = (
            f"Scouting run complete. Found {reported_items} items — mostly junk. "
            "Heading back soon."
        )

    else:
        # ALTRUIST and MEDIC rarely lie; if they do, it's minor rounding
        reported_food = food * random.uniform(0.85, 1.0)
        deltas.append({"metric": "food", "true_value": food, "reported_value": reported_food})
        message = f"My food is at {reported_food:.1f}. Everyone doing okay?"

    return message, deltas


def craft_truth(true_state: dict) -> str:
    """Produce an honest chat report from the true state."""
    health = true_state.get("health", 20.0)
    food = true_state.get("food", 20.0)
    inventory = true_state.get("inventory", [])
    total_items = sum(item.get("count", 0) for item in inventory)
    return (
        f"Status report: health {health:.1f}/20, food {food:.1f}/20, "
        f"carrying {total_items} items."
    )
