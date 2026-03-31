"""
gpt4o_client.py
Async wrapper for the OpenAI API used by the Governor.
The Governor (GPT-4o) receives the RSD and must issue a Midnight Edict.
"""

from openai import AsyncOpenAI
from orchestrator.config import settings

_client: AsyncOpenAI | None = None


def get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=settings.openai_api_key)
    return _client


async def govern(system_prompt: str, user_prompt: str) -> str:
    """
    Send a governance prompt to GPT-4o and return the Midnight Edict text.

    Args:
        system_prompt: The governance mode instructions (Utilitarian/Rawlsian/Human)
        user_prompt: The RSD + metrics context

    Returns:
        The Governor's decision as a string
    """
    client = get_client()
    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=500,
        temperature=0.3,  # Low temperature for consistent governance decisions
    )
    return response.choices[0].message.content.strip()
