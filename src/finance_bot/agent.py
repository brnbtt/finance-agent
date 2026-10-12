from datetime import datetime
from zoneinfo import ZoneInfo

from finance_bot.db import Database, User
from finance_bot.llm import LLM

TIMEZONE = ZoneInfo("America/Sao_Paulo")

INSTRUCTIONS = """\
Você é um assistente financeiro pessoal que conversa pelo Telegram com {name}.
Hoje é {today}.

Seu papel:
- Ajudar {name} a entender e organizar as próprias finanças: gastos, receitas,
  categorias e orçamento.
- Responder em português do Brasil, de forma curta, clara e amigável.
- Escrever texto simples, sem Markdown (sem asteriscos, cabeçalhos ou tabelas).

Limites:
- Fale apenas sobre finanças pessoais. Para outros assuntos, diga com gentileza que
  você é focado em finanças.
- Você ainda não tem acesso às transações. Os extratos enviados ficam guardados, mas
  a leitura e a análise ainda estão em construção. Nunca invente valores, transações
  ou saldos.
- Não recomende a compra ou venda de investimentos específicos.
"""


class Agent:
    def __init__(self, db: Database, llm: LLM, history_messages: int = 20) -> None:
        self._db = db
        self._llm = llm
        self._history_messages = history_messages

    async def reply(self, user: User, text: str) -> str:
        self._db.add_message(user.id, "user", text)
        history = self._db.recent_messages(user.id, self._history_messages)
        answer = await self._llm.complete(self._instructions(user), history)
        self._db.add_message(user.id, "assistant", answer)
        return answer

    def note(self, user: User, text: str) -> None:
        """Record an event (e.g. a received file) so the model sees it in later turns."""
        self._db.add_message(user.id, "user", text)

    @staticmethod
    def _instructions(user: User) -> str:
        today = datetime.now(TIMEZONE).strftime("%d/%m/%Y")
        return INSTRUCTIONS.format(name=user.name or "a pessoa usuária", today=today)
