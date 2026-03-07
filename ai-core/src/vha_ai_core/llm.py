from __future__ import annotations

from pathlib import Path

import httpx


class OllamaClient:
    def __init__(self, host: str, model: str, prompt_path: Path):
        self.host = host.rstrip("/")
        self.model = model
        self.prompt_path = prompt_path

    def system_prompt(self) -> str:
        if self.prompt_path.exists():
            return self.prompt_path.read_text(encoding="utf-8")
        return "Je bent Tukkie en spreekt Nederlands."

    def available(self) -> bool:
        try:
            response = httpx.get(f"{self.host}/api/tags", timeout=3.0)
            response.raise_for_status()
        except httpx.HTTPError:
            return False
        return True

    async def generate(self, *, user_prompt: str, context_prompt: str) -> str | None:
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.post(
                    f"{self.host}/api/chat",
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": self.system_prompt()},
                            {"role": "user", "content": f"Context:\n{context_prompt}\n\nVraag:\n{user_prompt}"},
                        ],
                        "stream": False,
                    },
                )
                response.raise_for_status()
                data = response.json()
        except (httpx.HTTPError, httpx.TimeoutException, ValueError):
            return None

        message = data.get("message", {})
        return message.get("content")
