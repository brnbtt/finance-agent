from pathlib import Path

from finance_bot.core import MAX_UPLOAD_BYTES, File, Text

FIXTURES = Path(__file__).parent / "fixtures"


async def test_csv_is_stored_and_noted_in_history(assistant, llm, ready_user):
    content = (FIXTURES / "picpay_demo_jul_ago_2026.csv").read_bytes()

    replies = await assistant.handle(File(ready_user, "picpay.csv", content))

    assert replies[0].startswith("Recebi picpay.csv")
    await assistant.handle(Text(ready_user, "recebeu?"))
    _, messages = llm.calls[-1]
    assert messages[0].content == "[Arquivo recebido: picpay.csv]"


async def test_duplicate_file_is_detected(assistant, ready_user):
    content = b"data,valor\n2026-07-01,10\n"
    await assistant.handle(File(ready_user, "a.csv", content))

    replies = await assistant.handle(File(ready_user, "renamed.csv", content))

    assert "já tinha recebido" in replies[0]


async def test_file_over_limit_is_rejected(assistant, ready_user):
    content = b"x" * (MAX_UPLOAD_BYTES + 1)

    replies = await assistant.handle(File(ready_user, "big.csv", content))

    assert "grande demais" in replies[0]


async def test_non_csv_is_rejected(assistant, ready_user):
    replies = await assistant.handle(File(ready_user, "extrato.pdf", b"%PDF-1.7"))

    assert "só leio extratos em CSV" in replies[0]
