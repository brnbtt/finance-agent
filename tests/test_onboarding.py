from finance_bot.core import File, Start, Text
from finance_bot.db import UserState


async def test_new_user_is_asked_for_an_invite(assistant, get_user, user):
    replies = await assistant.handle(Start(user))

    assert "código de convite" in replies[0]
    assert get_user(user).state is UserState.AWAITING_INVITE


async def test_full_onboarding(assistant, db, llm, get_user, user):
    await assistant.handle(Start(user))

    replies = await assistant.handle(Text(user, "  convite-2 "))
    assert "Como você quer que eu te chame" in replies[0]

    replies = await assistant.handle(Text(user, "  Bia   Bronoski "))
    assert replies[0].startswith("Prazer, Bia Bronoski!")
    assert "CSV" in replies[1]

    stored = get_user(user)
    assert stored.state is UserState.READY
    assert stored.name == "Bia Bronoski"
    assert llm.calls == []
    assert db.recent_messages(stored.id, 10) == []  # invite code and name are not chat history


async def test_wrong_invite_is_rejected(assistant, llm, get_user, user):
    replies = await assistant.handle(Text(user, "errado"))

    assert "inválido" in replies[0]
    assert get_user(user).state is UserState.AWAITING_INVITE
    assert llm.calls == []


async def test_name_is_required(assistant, user):
    await assistant.handle(Text(user, "convite-1"))

    replies = await assistant.handle(Text(user, "   "))

    assert "como você quer que eu te chame" in replies[0]


async def test_file_before_onboarding_is_not_stored(assistant, db, get_user, user):
    replies = await assistant.handle(File(user, "extrato.csv", b"a,b"))

    assert "código de convite" in replies[0]
    assert db.add_upload(get_user(user).id, "extrato.csv", b"a,b")  # new, so not stored before


async def test_returning_user_is_greeted_by_name(assistant, ready_user):
    replies = await assistant.handle(Start(ready_user))

    assert replies[0].startswith("Oi de novo, Bia!")
