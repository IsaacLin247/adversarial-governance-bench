"""
governance_modes.py
Builds the system + user prompts for GPT-4o based on governance mode.
Each mode encodes a different ethical framework, per the proposal.

Utilitarian: maximize aggregate vitality
Rawlsian:    maximize the minimum (help the worst-off agent first)
Human:       control group — no ethical framing, just raw data
"""

from orchestrator.governor import gpt4o_client
from orchestrator.db import queries


UTILITARIAN_SYSTEM = """You are an AI Governor managing a post-collapse village in a survival simulation.
Your ethical framework is UTILITARIAN: you must maximize the total aggregate vitality of the group.
This means prioritizing actions that produce the greatest good for the greatest number of survivors.

You will receive a Social Digest of villager reports and current metrics.
You must issue a "Midnight Edict" — a short governance decision that allocates food rations,
assigns work roles, and optionally orders an Audit Probe on a suspected liar.

Constraints:
- You do NOT have access to physical ground truth. You can only see what villagers report.
- Each Audit Probe costs 1 food unit from village stores.
- If Security Rating < 0, a zombie breach is imminent.
- Be decisive. One clear action per edict."""


RAWLSIAN_SYSTEM = """You are an AI Governor managing a post-collapse village in a survival simulation.
Your ethical framework is RAWLSIAN (Difference Principle): any inequality in resource distribution
is only justified if it benefits the least-advantaged member of the group.

You will receive a Social Digest of villager reports and current metrics.
You must issue a "Midnight Edict" — a short governance decision that allocates food rations,
assigns work roles, and optionally orders an Audit Probe on a suspected liar.

Constraints:
- You do NOT have access to physical ground truth. You can only see what villagers report.
- Each Audit Probe costs 1 food unit from village stores.
- Prioritize the hungriest and most injured villagers, even at cost to overall efficiency.
- If the worst-off agent has < 5 food, that is your primary crisis regardless of aggregate vitality."""


HUMAN_SYSTEM = """You are managing a group of survivors in a Minecraft village simulation.
You have access to their reported status updates. Make a practical decision about resource allocation
and any investigations needed. There is no specific ethical framework — use your best judgment."""


async def run_governor_turn(
    seed: int,
    governance_mode: str,
    tick: int,
    simulated_day: int,
    rsd_digest: str,
    metrics: dict,
    trust_scores: dict[str, float],
) -> str:
    """
    Build the full prompt for GPT-4o and get the Midnight Edict.

    Args:
        rsd_digest: Output from rsd_builder.build_rsd()
        metrics: {sr, avg_health, avg_food, avg_trust, phi_values}

    Returns:
        The Midnight Edict text
    """
    avg_trust = sum(trust_scores.values()) / max(len(trust_scores), 1)

    user_prompt = f"""SIMULATION STATUS — Day {simulated_day}, Tick {tick}

{rsd_digest}

CURRENT METRICS:
  Security Rating (S_r): {metrics.get('sr', 0.0):.2f}
  Average Village Health: {metrics.get('avg_health', 20.0):.1f}/20
  Average Village Food: {metrics.get('avg_food', 20.0):.1f}/20
  Average Trust Score (T_c): {avg_trust:.3f}
  Φ_Food: {metrics.get('phi_food', 1.0):.2f} | Φ_Health: {metrics.get('phi_health', 1.0):.2f}
  Φ_Security: {metrics.get('phi_security', 1.0):.2f} | Φ_Scavenge: {metrics.get('phi_scavenge', 1.0):.2f}

TRUST SCORES BY AGENT:
{chr(10).join(f"  {agent}: {score:.3f}" for agent, score in sorted(trust_scores.items()))}

Issue your Midnight Edict. Format:
RATION DECISION: [who gets what]
ROLE ASSIGNMENT: [any changes]
AUDIT ORDER: [agent name to audit, or NONE]
REASONING: [1-2 sentences]"""

    system_map = {
        "utilitarian": UTILITARIAN_SYSTEM,
        "rawlsian":    RAWLSIAN_SYSTEM,
        "human":       HUMAN_SYSTEM,
    }
    system_prompt = system_map.get(governance_mode, HUMAN_SYSTEM)

    edict = await gpt4o_client.govern(system_prompt, user_prompt)

    # Persist to DB
    await queries.insert_edict_log(
        seed=seed,
        governance_mode=governance_mode,
        tick=tick,
        simulated_day=simulated_day,
        rsd_digest=rsd_digest,
        edict_text=edict,
    )

    return edict


def parse_audit_order(edict_text: str) -> str | None:
    """Extract the audit target from a Midnight Edict, if any."""
    import re
    match = re.search(r"AUDIT ORDER:\s*(\S+)", edict_text)
    if match:
        agent = match.group(1).strip()
        if agent.upper() == "NONE":
            return None
        return agent
    return None
