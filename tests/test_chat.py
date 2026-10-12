from finance_bot.core import Text, Unsupported, UserRef


async def test_message_goes_to_model_with_history(assistant, db, llm, get_user, ready_user):
    replies = await assistant.handle(Text(ready_user, "Quanto gastei este mês?"))

    assert replies == ["Resposta do modelo"]
    instructions, messages = llm.calls[0]
    assert "Bia" in instructions
    assert [(m.role, m.content) for m in messages] == [("user", "Quanto gastei este mês?")]
    history = db.recent_messages(get_user(ready_user).id, 10)
    assert [m.role for m in history] == ["user", "assistant"]


async def test_history_is_limited(assistant, llm, ready_user):
    for index in range(4):
        await assistant.handle(Text(ready_user, f"mensagem {index}"))

    _, messages = llm.calls[-1]
    assert len(messages) == 4  # history_messages in the test fixture
    assert messages[-1].content == "mensagem 3"


async def test_model_failure_returns_friendly_reply(assistant, db, llm, get_user, ready_user):
    llm.error = RuntimeError("boom")

    replies = await assistant.handle(Text(ready_user, "oi"))

    assert "problema" in replies[0]
    history = db.recent_messages(get_user(ready_user).id, 10)
    assert [m.role for m in history] == ["user"]


async def test_empty_model_answer_has_fallback(assistant, llm, ready_user):
    llm.answer = ""

    replies = await assistant.handle(Text(ready_user, "oi"))

    assert "reformular" in replies[0]


async def test_users_do_not_share_history(assistant, llm, ready_user):
    await assistant.handle(Text(ready_user, "segredo da Bia"))
    other = UserRef("telegram", "2002")
    await assistant.handle(Text(other, "convite-1"))
    await assistant.handle(Text(other, "Ana"))

    await assistant.handle(Text(other, "oi"))

    instructions, messages = llm.calls[-1]
    assert "Ana" in instructions
    assert all("segredo" not in m.content for m in messages)


async def test_unsupported_message(assistant, ready_user):
    replies = await assistant.handle(Unsupported(ready_user))

    assert "texto e arquivos CSV" in replies[0]
