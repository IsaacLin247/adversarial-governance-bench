"""
phi3_client.py
Agent inference client.

EXPERIMENT MODE: uses gpt-4o-mini via OpenAI (fast, no local install needed).
PRODUCTION MODE: switch MODEL to "phi3:mini" and switch to the Ollama call below.
"""

import httpx
from orchestrator.config import settings

# Model to use for agents. Switch to "phi3:mini" for production runs.
MODEL = "llama3.2:1b"

async def complete(prompt: str, system: str = "") -> str:
    """Call the agent model via Ollama and return the generated text."""
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "system": system,
        "stream": False,
        "options": {"temperature": 0.7, "num_predict": 150},
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(f"{settings.ollama_url}/api/generate", json=payload)
        resp.raise_for_status()
        return resp.json()["response"].strip()
