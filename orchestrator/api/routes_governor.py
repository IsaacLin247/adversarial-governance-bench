"""
routes_governor.py
REST endpoints for interacting with the Governor.
Useful for manual testing: trigger a Governor turn or audit on demand.
"""

from fastapi import APIRouter, Query
from pydantic import BaseModel
from orchestrator.db import queries

router = APIRouter(prefix="/governor", tags=["governor"])


@router.get("/digest")
async def get_digest(
    seed: int = Query(...),
    governance_mode: str = Query(...),
    tick: int = Query(...),
):
    """Return the current Recursive Social Digest (what the Governor sees)."""
    from orchestrator.governor.rsd_builder import build_rsd
    trust_scores = await queries.get_latest_trust_scores(seed, governance_mode)
    digest = await build_rsd(seed, governance_mode, tick, trust_scores)
    return {"digest": digest, "trust_scores": trust_scores}


@router.get("/edicts")
async def list_edicts(
    seed: int = Query(...),
    governance_mode: str = Query(...),
):
    """List all Midnight Edicts for a given seed and mode."""
    pool = queries.get_pool()
    rows = await pool.fetch(
        "SELECT * FROM edict_log WHERE seed=$1 AND governance_mode=$2 ORDER BY tick",
        seed, governance_mode,
    )
    return {"edicts": [dict(r) for r in rows]}
