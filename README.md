# Finance Bot

A personal finance assistant on Telegram. Users send bank exports (CSV) and ask questions in
natural language; an LLM (GPT-6 Luna on Azure AI Foundry) answers.

Status: onboarding, CSV uploads, and chat work; reading transactions and analysis come next. See
[docs/next-steps.md](docs/next-steps.md).

## Layout

```text
src/finance_bot/
  __main__.py      # entry point: wiring + Telegram long polling
  config.py        # settings from environment / .env
  telegram_bot.py  # Telegram adapter: updates -> core events, replies -> messages
  core.py          # channel-agnostic: onboarding, routing, uploads
  agent.py         # model conversation: instructions + history
  llm.py           # Azure AI Foundry client (Responses API)
  db.py            # SQLite schema, migrations, queries
tests/             # pytest with a fake model; fictional CSV fixtures
```

## Setup

Requires [uv](https://docs.astral.sh/uv/) and Python 3.12+.

```bash
uv sync
cp .env.example .env   # then fill in the values
```

You need a bot token from [@BotFather](https://t.me/BotFather), invite codes of your choice, and
an Azure AI Foundry resource with a `gpt-6-luna` deployment. Without an API key the bot uses
Entra ID: run `az login` and give your user the `Cognitive Services OpenAI User` role.

## Run and test

```bash
uv run finance-bot     # then /start in Telegram, the invite code, and your name
uv run pytest
uv run ruff check .
```

## Data

Real data lives only in `data/` (ignored by Git). Never commit statements, databases, or `.env`.
See [SECURITY.md](SECURITY.md).
