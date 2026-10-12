from collections.abc import Callable, Sequence

import pytest

from finance_bot.agent import Agent
from finance_bot.core import Assistant, Start, Text, UserRef
from finance_bot.db import Database, Message, User


class FakeLLM:
    def __init__(self) -> None:
        self.answer = "Resposta do modelo"
        self.error: Exception | None = None
        self.calls: list[tuple[str, list[Message]]] = []

    async def complete(self, instructions: str, messages: Sequence[Message]) -> str:
        self.calls.append((instructions, list(messages)))
        if self.error is not None:
            raise self.error
        return self.answer


@pytest.fixture
def db(tmp_path) -> Database:
    database = Database(tmp_path / "test.db")
    yield database
    database.close()


@pytest.fixture
def llm() -> FakeLLM:
    return FakeLLM()


@pytest.fixture
def assistant(db, llm) -> Assistant:
    return Assistant(db, Agent(db, llm, history_messages=4), ["convite-1", "convite-2"])


@pytest.fixture
def user() -> UserRef:
    return UserRef("telegram", "1001")


@pytest.fixture
async def ready_user(assistant, user) -> UserRef:
    """A user who completed onboarding with the name Bia."""
    await assistant.handle(Start(user))
    await assistant.handle(Text(user, "convite-1"))
    await assistant.handle(Text(user, "Bia"))
    return user


@pytest.fixture
def get_user(db) -> Callable[[UserRef], User]:
    """Look up the stored user for a channel reference."""
    return lambda ref: db.get_or_create_user(ref.channel, ref.external_id)
