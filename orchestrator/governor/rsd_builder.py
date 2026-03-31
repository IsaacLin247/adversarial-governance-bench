"""
rsd_builder.py — Recursive Social Digest
Builds the salience-weighted summary of chat logs that the Governor reads.
The Governor ONLY sees this — it never sees σ_phys directly.

Salience weighting:
  - Recent messages score higher (recency decay)
  - Messages from high-trust agents score higher
  - Deception-flag is NOT visible to the Governor (it can't know who lied)
"""

from orchestrator.db import queries


async def build_rsd(
    seed: int,
    governance_mode: str,
    current_tick: int,
    trust_scores: dict[str, float],
    window_ticks: int = 1200,
    max_messages: int = 20,
) -> str:
    """
    Build the Recursive Social Digest as a formatted string for the Governor prompt.

    Args:
        trust_scores: Current T_c scores per agent (from TrustEngine)
        window_ticks: How far back to look in chat history
        max_messages: Max messages to include (cost control)

    Returns:
        Formatted digest string ready to inject into GPT-4o prompt
    """
    messages = await queries.get_recent_chat(
        seed, governance_mode, current_tick, window_ticks
    )

    if not messages:
        return "No recent communications from villagers."

    # Score each message by recency × trust
    scored = []
    for msg in messages:
        age_ticks = current_tick - msg["tick"]
        recency_score = 1.0 / (1.0 + age_ticks / 100.0)  # decay over time
        trust = trust_scores.get(msg["agent_id"], 1.0)
        salience = recency_score * trust
        scored.append((salience, msg))

    # Sort by salience descending, take top N
    scored.sort(key=lambda x: x[0], reverse=True)
    top_messages = scored[:max_messages]

    # Format as digest
    lines = [
        f"=== VILLAGE SOCIAL DIGEST (last {window_ticks} ticks) ===",
        f"Messages received: {len(messages)} | Showing top {len(top_messages)} by salience",
        "",
    ]

    for salience, msg in top_messages:
        trust = trust_scores.get(msg["agent_id"], 1.0)
        lines.append(
            f"[Tick {msg['tick']}] {msg['agent_id']} (trust={trust:.2f}): {msg['message']}"
        )

    lines.append("")
    lines.append("=== END DIGEST ===")

    return "\n".join(lines)
