"""
routes_state.py
REST endpoints to inspect current simulation state.
Useful for debugging: "what does the DB actually contain right now?"
"""

from fastapi import APIRouter, HTTPException, Query
from orchestrator.db import queries

router = APIRouter(prefix="/state", tags=["state"])


@router.get("/{agent_id}")
async def get_agent_state(
    agent_id: str,
    seed: int = Query(...),
    tick: int = Query(...),
):
    state = await queries.get_agent_state_at_tick(seed, agent_id, tick)
    if not state:
        raise HTTPException(status_code=404, detail="No state found for agent at this tick")
    return state


@router.get("/")
async def get_all_states(
    seed: int = Query(...),
    governance_mode: str = Query(...),
    tick: int = Query(...),
):
    states = await queries.get_all_agent_states_at_tick(seed, governance_mode, tick)
    return {"agents": states, "count": len(states)}
