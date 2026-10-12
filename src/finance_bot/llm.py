from collections.abc import Sequence
from typing import Protocol

from azure.identity.aio import DefaultAzureCredential, get_bearer_token_provider
from openai import AsyncOpenAI

from finance_bot.db import Message

AZURE_SCOPE = "https://cognitiveservices.azure.com/.default"


class LLM(Protocol):
    async def complete(self, instructions: str, messages: Sequence[Message]) -> str: ...


class FoundryLLM:
    """Azure AI Foundry deployment called through the OpenAI-compatible v1 Responses API."""

    def __init__(self, endpoint: str, deployment: str, api_key: str | None = None) -> None:
        self._deployment = deployment
        self._credential: DefaultAzureCredential | None = None
        if api_key:
            auth = api_key
        else:
            self._credential = DefaultAzureCredential()
            auth = get_bearer_token_provider(self._credential, AZURE_SCOPE)
        self._client = AsyncOpenAI(base_url=f"{endpoint.rstrip('/')}/openai/v1/", api_key=auth)

    async def complete(self, instructions: str, messages: Sequence[Message]) -> str:
        response = await self._client.responses.create(
            model=self._deployment,
            instructions=instructions,
            input=[{"role": message.role, "content": message.content} for message in messages],
            reasoning={"effort": "low"},
            store=False,
        )
        return response.output_text.strip()

    async def close(self) -> None:
        await self._client.close()
        if self._credential is not None:
            await self._credential.close()
