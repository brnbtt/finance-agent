import logging
from dataclasses import dataclass

from finance_bot.agent import Agent
from finance_bot.db import Database, User, UserState

logger = logging.getLogger(__name__)

MAX_UPLOAD_BYTES = 5 * 1024 * 1024


@dataclass(frozen=True)
class UserRef:
    channel: str
    external_id: str


@dataclass(frozen=True)
class Start:
    user: UserRef


@dataclass(frozen=True)
class Text:
    user: UserRef
    text: str


@dataclass(frozen=True)
class File:
    user: UserRef
    filename: str
    content: bytes


@dataclass(frozen=True)
class Unsupported:
    user: UserRef


Event = Start | Text | File | Unsupported


class Assistant:
    """Channel-agnostic entry point: one event in, zero or more reply texts out."""

    def __init__(self, db: Database, agent: Agent, invite_codes: list[str]) -> None:
        self._db = db
        self._agent = agent
        self._invite_codes = invite_codes

    async def handle(self, event: Event) -> list[str]:
        user = self._db.get_or_create_user(event.user.channel, event.user.external_id)
        if user.state is UserState.AWAITING_INVITE:
            return self._handle_invite(user, event)
        if user.state is UserState.AWAITING_NAME:
            return self._handle_name(user, event)

        match event:
            case Start():
                return [
                    f"Oi de novo, {user.name}! Me manda um extrato em CSV ou uma pergunta "
                    "sobre suas finanças."
                ]
            case Text(text=text):
                return [await self._chat(user, text)]
            case File():
                return [self._receive_file(user, event)]
            case _:
                return ["Por enquanto eu entendo mensagens de texto e arquivos CSV."]

    # Onboarding is plain code and never reaches the model.

    def _handle_invite(self, user: User, event: Event) -> list[str]:
        if not isinstance(event, Text):
            return [
                "Oi! Eu sou um assistente financeiro pessoal. Para começar, me manda o seu "
                "código de convite."
            ]
        if event.text.strip() not in self._invite_codes:
            return ["Código inválido. Confere e me manda de novo?"]
        self._db.update_user(user.id, UserState.AWAITING_NAME)
        return ["Código aceito! Como você quer que eu te chame?"]

    def _handle_name(self, user: User, event: Event) -> list[str]:
        name = " ".join(event.text.split()) if isinstance(event, Text) else ""
        if not name:
            return ["Antes de tudo, como você quer que eu te chame?"]
        self._db.update_user(user.id, UserState.READY, name=name)
        return [
            f"Prazer, {name}! 😊",
            "Agora me manda seus extratos bancários em CSV, de qualquer banco. Também pode me "
            "perguntar o que quiser sobre suas finanças.",
        ]

    async def _chat(self, user: User, text: str) -> str:
        try:
            answer = await self._agent.reply(user, text)
        except Exception as exc:
            # Type only: exception text can echo request content.
            logger.error("model call failed for user %s: %s", user.id, type(exc).__name__)
            return "Tive um problema para responder agora. Tenta de novo em instantes?"
        return answer or "Hmm, não consegui formular uma resposta. Pode reformular?"

    def _receive_file(self, user: User, event: File) -> str:
        if not event.filename.lower().endswith(".csv"):
            return "Por enquanto eu só leio extratos em CSV."
        if len(event.content) > MAX_UPLOAD_BYTES:
            return f"Esse arquivo é grande demais. O limite é {MAX_UPLOAD_BYTES // 2**20} MB."
        if not self._db.add_upload(user.id, event.filename, event.content):
            return "Esse arquivo eu já tinha recebido."
        self._agent.note(user, f"[Arquivo recebido: {event.filename}]")
        return (
            f"Recebi {event.filename} e guardei aqui. A leitura dos lançamentos ainda está em "
            "construção; em breve eu consigo analisar."
        )
