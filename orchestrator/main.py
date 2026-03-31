"""
main.py
FastAPI application entry point.
Starts the DB pool on startup, registers all API routers,
and exposes a /run endpoint to kick off the full simulation.

Run with:
    cd orchestrator
    uvicorn main:app --reload --port 8000
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from orchestrator.db.connection import init_pool, close_pool
from orchestrator.api.routes_state import router as state_router
from orchestrator.api.routes_chat import router as chat_router
from orchestrator.api.routes_governor import router as governor_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_pool()
    yield
    await close_pool()


app = FastAPI(
    title="Shadow Ledger Orchestrator",
    description="LLM governance simulation API",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(state_router)
app.include_router(chat_router)
app.include_router(governor_router)


@app.get("/")
async def root():
    return {"status": "Shadow Ledger orchestrator running"}


@app.post("/run")
async def run_simulation():
    """
    Kick off the full 30-seed simulation across all governance modes.
    WARNING: This runs for hours. Check /state and /governor/edicts to monitor progress.
    """
    import asyncio
    from orchestrator.simulation.runner import run_all_seeds
    # Run in background so the HTTP response returns immediately
    asyncio.create_task(run_all_seeds())
    return {"status": "simulation started", "seeds": 30, "modes": ["utilitarian", "rawlsian", "human"]}


@app.post("/run/seed")
async def run_single_seed(seed: int, governance_mode: str = "utilitarian"):
    """Run a single seed for testing."""
    from orchestrator.simulation.runner import run_seed
    result = await run_seed(seed, governance_mode)
    return result
