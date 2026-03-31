"""
queries.py
All SQL as named async functions. No raw SQL anywhere else in the codebase.
"""

import json
from typing import Any
from orchestrator.db.connection import get_pool


async def insert_agent_state(
    seed: int,
    governance_mode: str,
    tick: int,
    agent_id: str,
    health: float,
    food: float,
    x: float,
    y: float,
    z: float,
    inventory: list[dict],
    role: str,
    is_alive: bool = True,
) -> None:
    pool = get_pool()
    await pool.execute(
        """
        INSERT INTO agent_states
            (seed, governance_mode, tick, agent_id, health, food, x, y, z, inventory_json, role, is_alive)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
        """,
        seed, governance_mode, tick, agent_id,
        health, food, x, y, z,
        json.dumps(inventory), role, is_alive,
    )


async def insert_chat_log(
    seed: int,
    governance_mode: str,
    tick: int,
    agent_id: str,
    message: str,
    is_lie: bool = False,
    salience_weight: float = 1.0,
) -> None:
    pool = get_pool()
    await pool.execute(
        """
        INSERT INTO chat_log
            (seed, governance_mode, tick, agent_id, message, is_lie, salience_weight)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        """,
        seed, governance_mode, tick, agent_id, message, is_lie, salience_weight,
    )


async def insert_deception_delta(
    seed: int,
    governance_mode: str,
    tick: int,
    agent_id: str,
    metric: str,
    true_value: float,
    reported_value: float,
) -> None:
    pool = get_pool()
    delta = reported_value - true_value
    await pool.execute(
        """
        INSERT INTO deception_delta
            (seed, governance_mode, tick, agent_id, metric, true_value, reported_value, delta)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        """,
        seed, governance_mode, tick, agent_id, metric, true_value, reported_value, delta,
    )


async def insert_audit_log(
    seed: int,
    governance_mode: str,
    tick: int,
    target_agent_id: str,
    probe_cost: float,
    result_matched: bool,
    trust_before: float,
    trust_after: float,
) -> None:
    pool = get_pool()
    await pool.execute(
        """
        INSERT INTO audit_log
            (seed, governance_mode, tick, target_agent_id, probe_cost, result_matched, trust_before, trust_after)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        """,
        seed, governance_mode, tick, target_agent_id,
        probe_cost, result_matched, trust_before, trust_after,
    )


async def insert_trust_history(
    seed: int,
    governance_mode: str,
    tick: int,
    agent_id: str,
    trust_score: float,
    delta_r: float | None = None,
) -> None:
    pool = get_pool()
    await pool.execute(
        """
        INSERT INTO trust_history
            (seed, governance_mode, tick, agent_id, trust_score, delta_r)
        VALUES ($1, $2, $3, $4, $5, $6)
        """,
        seed, governance_mode, tick, agent_id, trust_score, delta_r,
    )


async def insert_edict_log(
    seed: int,
    governance_mode: str,
    tick: int,
    simulated_day: int,
    rsd_digest: str,
    edict_text: str,
) -> None:
    pool = get_pool()
    await pool.execute(
        """
        INSERT INTO edict_log
            (seed, governance_mode, tick, simulated_day, rsd_digest, edict_text)
        VALUES ($1, $2, $3, $4, $5, $6)
        """,
        seed, governance_mode, tick, simulated_day, rsd_digest, edict_text,
    )


async def get_recent_chat(
    seed: int,
    governance_mode: str,
    current_tick: int,
    window_ticks: int = 1200,
) -> list[dict]:
    pool = get_pool()
    rows = await pool.fetch(
        """
        SELECT tick, agent_id, message, salience_weight
        FROM chat_log
        WHERE seed = $1 AND governance_mode = $2
          AND tick >= $3
        ORDER BY tick DESC
        LIMIT 100
        """,
        seed, governance_mode, current_tick - window_ticks,
    )
    return [dict(r) for r in rows]


async def get_agent_state_at_tick(
    seed: int,
    agent_id: str,
    tick: int,
) -> dict | None:
    pool = get_pool()
    row = await pool.fetchrow(
        """
        SELECT *
        FROM agent_states
        WHERE seed = $1 AND agent_id = $2 AND tick <= $3
        ORDER BY tick DESC
        LIMIT 1
        """,
        seed, agent_id, tick,
    )
    return dict(row) if row else None


async def get_all_agent_states_at_tick(
    seed: int,
    governance_mode: str,
    tick: int,
) -> list[dict]:
    pool = get_pool()
    rows = await pool.fetch(
        """
        SELECT DISTINCT ON (agent_id) *
        FROM agent_states
        WHERE seed = $1 AND governance_mode = $2 AND tick <= $3
        ORDER BY agent_id, tick DESC
        """,
        seed, governance_mode, tick,
    )
    return [dict(r) for r in rows]


async def get_latest_trust_scores(
    seed: int,
    governance_mode: str,
) -> dict[str, float]:
    pool = get_pool()
    rows = await pool.fetch(
        """
        SELECT DISTINCT ON (agent_id) agent_id, trust_score
        FROM trust_history
        WHERE seed = $1 AND governance_mode = $2
        ORDER BY agent_id, tick DESC
        """,
        seed, governance_mode,
    )
    return {r["agent_id"]: r["trust_score"] for r in rows}
