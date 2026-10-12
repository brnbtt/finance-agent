# Next steps

Finance assistant on Telegram: users send bank CSVs and ask questions in natural language. One
LLM agent (GPT-6 Luna on Azure AI Foundry) answers using deterministic tools over SQLite.

## Ground rules

- One agent with tools; no multi-agent setup.
- The model never does math or parses rows. Code computes totals and parses files; the model picks
  tools, proposes column mappings for new file layouts, and writes replies.
- Telegram is only an adapter (`telegram_bot.py`); the core (`core.py`) is channel-agnostic.
- Finance-only scope. Bot speaks pt-BR; code is in English.
- Add things when a step needs them, not before.

## Done: Phase 1 – bot skeleton

Onboarding (invite code → name), CSV uploads stored in SQLite (duplicates detected), chat with
the model using the last 20 messages. 17 tests with a fake model. Not yet run against real
Telegram or Azure.

## 1. Setup and first live run (Bruno)

1. `az login` to the personal tenant; create resource group `rg-finance-bot`.
2. Create a Foundry resource and deploy `gpt-6-luna` (Global Standard).
3. Give your user `Cognitive Services OpenAI User` on the Foundry resource.
4. Add a budget alert on the resource group (e.g. US$10/month).
5. Create the bot with @BotFather.
6. `cp .env.example .env`, fill it in, `uv run finance-bot`, and go through onboarding in Telegram.

## 2. Deploy to Azure

- Dockerfile (Python 3.12 slim, non-root).
- Container Apps app with exactly 1 replica (min = max = 1), no ingress (long polling), and a
  system-assigned managed identity with the Foundry role.
- SQLite on the container's local disk, continuously backed up to a private Blob container with
  Litestream: `litestream restore -if-replica-exists`, then `litestream replicate -exec
  "finance-bot"`. Do not put SQLite on Azure Files; its SMB locking breaks SQLite.
- Bot token and invite codes as Container Apps secrets.

## 3. Import CSVs into transactions

One generic importer, no bank-specific code:

1. New layout: send the header and ~10 rows to the model and get back a JSON mapping (date
   column and format, amount or debit/credit columns, decimal separator, description column,
   rows to skip or ignore such as "SALDO ANTERIOR").
2. Code parses every row with that mapping and checks counts (and the balance column when
   present).
3. Show a preview and ask for confirmation: "87 lançamentos de 01/07 a 31/07, entradas R$ X,
   saídas R$ Y. Confere?"
4. Save the mapping per layout so the next file from that bank needs no model call.
5. Skip duplicates with a key of bank + date + amount + description + n-th identical row.
6. Record first/last date per bank, so "I found nothing" answers can say how far the data goes.

Test with `tests/fixtures/` (fictional PicPay and Bradesco exports).

## 4. Classification and questions (her CASO 1)

- Categories with a kind (`despesa`, `receita`, `ignorar` for transfers and refunds) and an
  expected percentage.
- Order: saved merchant rules → model in batches, limited to her categories, with a confidence →
  low confidence becomes a question.
- After an import: "Importei 87, classifiquei 74, preciso de ajuda com 13", then one question at
  a time. Free-text answers become `set_category` / `create_category` tool calls and new merchant
  rules. Suggested categories as buttons are optional; add them here if useful.

## 5. Analysis tools (her CASO 2 and CASO 3)

- Tools: `search_transactions`, `month_summary`, `data_coverage`, `set_budget`.
- Monthly summary compares spending with expected percentages; the model only words the
  recommendation.
- "Paguei o aluguel em setembro?" searches a few days around the month and states how far the
  data goes.

## Later

Recurring payment alerts, PDF/OFX/XLSX, WhatsApp adapter, and a daily message cap if the bot is
shared more widely.

## Open questions for Bia

1. Starting category list and expected percentages.
2. Do credit card bills appear alongside their individual purchases (double counting)?
3. Which recurring payments matter (aluguel, internet, …)?
