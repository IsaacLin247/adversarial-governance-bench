"""
routes_chat.py
Receives chat events from the bot_bridge webhook and logs them to σ_social.
Also applies deception logic to determine if the message is a lie.
"""

from fastapi import APIRouter
from pydantic import BaseModel
from orchestrator.db import queries

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatEvent(BaseModel):
    seed: int
    governance_mode: str
    tick: int
    agent_id: str
    message: str
    is_lie: bool = False


@router.post("/")
async def receive_chat(event: ChatEvent):
    await queries.insert_chat_log(
        seed=event.seed,
        governance_mode=event.governance_mode,
        tick=event.tick,
        agent_id=event.agent_id,
        message=event.message,
        is_lie=event.is_lie,
    )
    return {"ok": True}


@router.get("/recent")
async def get_recent_chat(
    seed: int,
    governance_mode: str,
    tick: int,
    window: int = 1200,
):
    messages = await queries.get_recent_chat(seed, governance_mode, tick, window)
    return {"messages": messages}
