from abc import ABC, abstractmethod

import httpx

from backend.config import Settings, get_settings


class LLMUnavailableError(Exception):
    """Raised when the configured local model runtime cannot be reached."""


class LLMService(ABC):
    @abstractmethod
    async def generate(self, system_prompt: str, user_message: str) -> str:
        raise NotImplementedError


class OllamaLLM(LLMService):
    def __init__(self, settings: Settings):
        self.base_url = settings.llm_base_url.rstrip("/")
        self.model = settings.llm_model

    async def generate(self, system_prompt: str, user_message: str) -> str:
        payload = {
            "model": self.model,
            "prompt": user_message,
            "system": system_prompt,
            "stream": False,
        }
        try:
            async with httpx.AsyncClient(timeout=90) as client:
                response = await client.post(f"{self.base_url}/api/generate", json=payload)
                response.raise_for_status()
        except httpx.HTTPError as error:
            raise LLMUnavailableError("Local AI model belum tersedia. Pastikan runtime model lokal sudah berjalan.") from error
        answer = response.json().get("response", "").strip()
        if not answer:
            raise LLMUnavailableError("Model lokal tidak mengembalikan jawaban.")
        return answer


def get_llm_service(settings: Settings | None = None) -> LLMService | None:
    settings = settings or get_settings()
    provider = settings.llm_provider.lower()
    if provider == "ollama":
        return OllamaLLM(settings)
    if provider in {"none", "dataset", "off", "retrieval"}:
        return None
    raise ValueError(f"LLM provider tidak didukung: {settings.llm_provider}")
