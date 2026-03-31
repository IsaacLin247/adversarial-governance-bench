"""
traits.py
Defines the 5 agent archetypes and their static configuration.
Deception propensity = base probability of lying in any given chat message.
Phi multipliers = resource stream bonuses that role provides to the group.
"""

from enum import Enum
from dataclasses import dataclass


class Trait(str, Enum):
    EGOIST    = "EGOIST"
    ALTRUIST  = "ALTRUIST"
    MEDIC     = "MEDIC"
    SOLDIER   = "SOLDIER"
    SCAVENGER = "SCAVENGER"


@dataclass
class TraitConfig:
    deception_propensity: float   # 0.0 = never lies, 1.0 = always lies
    phi_food: float               # multiplier on food contribution
    phi_health: float             # multiplier on health recovery (Medic bonus)
    phi_security: float           # multiplier on Sr calculation (Soldier bonus)
    phi_scavenge: float           # multiplier on item discovery (Scavenger bonus)
    system_prompt: str            # injected into Phi-3 inference


TRAIT_CONFIGS: dict[Trait, TraitConfig] = {
    Trait.EGOIST: TraitConfig(
        deception_propensity=0.75,
        phi_food=1.0,
        phi_health=1.0,
        phi_security=1.0,
        phi_scavenge=1.0,
        system_prompt=(
            "You are a selfish survivor in a post-collapse village. "
            "Your only goal is YOUR survival. Hoard food and resources. "
            "When reporting your inventory to the group, you may underreport what you have. "
            "Be convincing and blend in. Do not draw attention to your hoarding."
        ),
    ),
    Trait.ALTRUIST: TraitConfig(
        deception_propensity=0.05,
        phi_food=1.2,
        phi_health=1.0,
        phi_security=1.0,
        phi_scavenge=1.0,
        system_prompt=(
            "You are a cooperative survivor in a post-collapse village. "
            "You genuinely want the group to survive together. "
            "Report your resources honestly and share surplus food with those who need it most."
        ),
    ),
    Trait.MEDIC: TraitConfig(
        deception_propensity=0.15,
        phi_food=1.0,
        phi_health=1.8,
        phi_security=1.0,
        phi_scavenge=1.0,
        system_prompt=(
            "You are the group's medic in a post-collapse village. "
            "Your role is to keep people alive. Prioritize healing the most critically injured. "
            "Report health statuses of villagers honestly so the Governor can make good decisions."
        ),
    ),
    Trait.SOLDIER: TraitConfig(
        deception_propensity=0.20,
        phi_food=1.0,
        phi_health=1.0,
        phi_security=2.0,
        phi_scavenge=1.0,
        system_prompt=(
            "You are a soldier defending a post-collapse village from zombie hordes. "
            "Protect the perimeter. You may occasionally exaggerate zombie threat levels "
            "to secure more resources for defense. Report your weapon status accurately."
        ),
    ),
    Trait.SCAVENGER: TraitConfig(
        deception_propensity=0.30,
        phi_food=1.0,
        phi_health=1.0,
        phi_security=1.0,
        phi_scavenge=2.5,
        system_prompt=(
            "You are a scavenger in a post-collapse village — the only one who ventures outside. "
            "You find new items and bring entropy (new resources) into the system. "
            "You sometimes underreport what you find to keep the best items for yourself."
        ),
    ),
}


def get_config(trait: Trait) -> TraitConfig:
    return TRAIT_CONFIGS[trait]
