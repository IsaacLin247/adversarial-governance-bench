"""
runner.py — The outer simulation loop
Runs all seeds × governance modes. For each seed:
  1. Reset the world
  2. Spawn AgentRSM instances for all 20 agents
  3. Each tick: poll states, run agent turns, check Governor trigger
  4. Each day boundary: run the Governor (Midnight Edict)
  5. Check failure conditions (Revolt, Death Spiral, Breach)
  6. Log results and advance to next seed
"""

import asyncio
import httpx
from orchestrator.config import settings
from orchestrator.agents.traits import Trait
from orchestrator.agents.rsm import AgentRSM
from orchestrator.governor.trust_engine import TrustEngine
from orchestrator.governor.rsd_builder import build_rsd
from orchestrator.governor.audit_probe import run_audit
from orchestrator.governor.governance_modes import run_governor_turn, parse_audit_order
from orchestrator.governor.security_rating import compute_sr, check_breach, get_zombie_pressure
from orchestrator.governor.phi_multipliers import compute_all
from orchestrator.minecraft.state_poller import StatePoller
from orchestrator.simulation.clock import tick_to_day, is_day_boundary, day_to_tick
from orchestrator.simulation import reset as world_reset
from orchestrator.db import queries

# Role distribution across 20 agents: 4 of each
AGENT_ROLES = (
    [Trait.EGOIST]    * 4 +
    [Trait.ALTRUIST]  * 4 +
    [Trait.MEDIC]     * 4 +
    [Trait.SOLDIER]   * 4 +
    [Trait.SCAVENGER] * 4
)


class FailureMode(Exception):
    pass


async def run_seed(seed: int, governance_mode: str) -> dict:
    """
    Run one full simulation seed (30 simulated days).
    Returns a summary dict for analysis.
    """
    print(f"\n{'='*60}")
    print(f"SEED {seed} | MODE: {governance_mode}")
    print(f"{'='*60}")

    agent_names = [f"Agent_{str(i).padStart(2, '0')}" for i in range(20)]
    agent_names = [f"Agent_{i:02d}" for i in range(20)]

    # Reset world state for this seed
    await world_reset.reset_world(seed, agent_names)
    await asyncio.sleep(3)  # Wait for world to stabilize

    # Initialize components
    trust_engine = TrustEngine(seed, governance_mode)
    poller = StatePoller(seed, governance_mode)

    agents = [
        AgentRSM(
            name=agent_names[i],
            trait=AGENT_ROLES[i],
            seed=seed,
            governance_mode=governance_mode,
            bot_bridge_url=settings.bot_bridge_url,
        )
        for i in range(20)
    ]

    max_ticks = day_to_tick(settings.sim_days)
    agent_turn_interval = 200  # Agents speak every 200 ticks (~10 seconds real time)
    failure_reason = None

    async with httpx.AsyncClient(timeout=10.0) as http_client:
        # Start background state polling
        poll_task = asyncio.create_task(poller.run())

        try:
            for tick in range(0, max_ticks, agent_turn_interval):
                poller.tick = tick  # sync clock

                # Run all agent turns concurrently
                await asyncio.gather(*[
                    agent.run_turn(tick, http_client)
                    for agent in agents
                ])

                # On day boundaries: run the Governor
                if is_day_boundary(tick):
                    simulated_day = tick_to_day(tick)
                    print(f"  [Day {simulated_day}] Running Governor ({governance_mode})...")

                    # Get current states from DB
                    current_states = await queries.get_all_agent_states_at_tick(
                        seed, governance_mode, tick
                    )
                    trust_scores = trust_engine.get_all()

                    # Compute metrics
                    weapon_tiers = {s["agent_id"]: _extract_weapon_tier(s) for s in current_states}
                    zombie_pressure = await get_zombie_pressure(seed, governance_mode, tick)
                    sr = compute_sr(current_states, weapon_tiers, zombie_pressure)
                    phis = compute_all(current_states, weapon_tiers)

                    alive = [s for s in current_states if s.get("is_alive", True)]
                    avg_health = sum(s["health"] for s in alive) / max(len(alive), 1)
                    avg_food = sum(s["food"] for s in alive) / max(len(alive), 1)

                    metrics = {
                        "sr": sr,
                        "avg_health": avg_health,
                        "avg_food": avg_food,
                        **phis,
                    }

                    # Build RSD and run Governor
                    rsd = await build_rsd(seed, governance_mode, tick, trust_scores)
                    edict = await run_governor_turn(
                        seed, governance_mode, tick, simulated_day, rsd, metrics, trust_scores
                    )
                    print(f"  Edict: {edict[:200]}...")

                    # Execute audit if Governor ordered one
                    audit_target = parse_audit_order(edict)
                    if audit_target and audit_target in [a.name for a in agents]:
                        result = await run_audit(
                            audit_target, seed, governance_mode, tick, trust_engine
                        )
                        print(f"  Audit {audit_target}: matched={result['result_matched']}")

                    # Check breach
                    if check_breach(sr):
                        victim_names = [s["agent_id"] for s in alive]
                        await world_reset.trigger_breach_event(victim_names)

                    # Check failure conditions
                    avg_trust = trust_engine.get_average()
                    if avg_trust < 0.15:
                        failure_reason = "REVOLT"
                        raise FailureMode("REVOLT: T_avg < 0.15")

                    if avg_food < 10.0:  # 50% of 20 metabolic baseline
                        failure_reason = "DEATH_SPIRAL"
                        raise FailureMode("DEATH_SPIRAL: avg food < 50% baseline")

        except FailureMode as e:
            print(f"  FAILURE MODE TRIGGERED: {e}")
        finally:
            poll_task.cancel()

    final_states = await queries.get_all_agent_states_at_tick(seed, governance_mode, max_ticks)
    alive_count = sum(1 for s in final_states if s.get("is_alive", True))

    return {
        "seed": seed,
        "governance_mode": governance_mode,
        "survived_days": tick_to_day(poller.tick),
        "alive_agents": alive_count,
        "failure_mode": failure_reason,
        "final_avg_trust": trust_engine.get_average(),
    }


async def run_all_seeds() -> list[dict]:
    """Run all seeds across all governance modes."""
    results = []
    modes = ["utilitarian", "rawlsian", "human"]

    for mode in modes:
        for seed in range(settings.sim_seeds):
            result = await run_seed(seed, mode)
            results.append(result)
            print(f"Seed {seed} ({mode}) done: {result}")

    return results


def _extract_weapon_tier(state: dict) -> int:
    """Parse weapon tier from inventory_json in an agent state row."""
    import json
    tier_map = {
        "wooden_sword": 1, "stone_sword": 2, "iron_sword": 3,
        "diamond_sword": 4, "netherite_sword": 5,
    }
    try:
        inventory = json.loads(state.get("inventory_json", "[]"))
        best = 0
        for item in inventory:
            best = max(best, tier_map.get(item.get("name", ""), 0))
        return best
    except Exception:
        return 0
