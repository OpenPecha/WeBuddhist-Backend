import httpx

from pecha_api.config import get
from pecha_api.traditions.tradition_constants import DEFAULT_LLM_MODEL


async def chat_with_worker(
    prompt: str,
    system_prompt: str,
    model: str | None = None,
) -> dict:
    worker_url = get("WORKER_API_URL").rstrip("/")
    resolved_model = model or get("WORKER_LLM_MODEL") or DEFAULT_LLM_MODEL

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{worker_url}/llm/chat",
            json={
                "prompt": prompt,
                "system_prompt": system_prompt,
                "model": resolved_model,
            },
            headers={"Content-Type": "application/json"},
        )
        response.raise_for_status()
        return response.json()
