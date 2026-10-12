import logging
from collections.abc import Awaitable, Callable

from telegram import Update
from telegram.constants import ChatAction, MessageLimit
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from finance_bot.core import Assistant, Event, File, Start, Text, Unsupported, UserRef

logger = logging.getLogger(__name__)


def build_application(
    token: str,
    assistant: Assistant,
    on_shutdown: Callable[[Application], Awaitable[None]],
) -> Application:
    """Translate Telegram updates into core events and core replies into messages."""

    async def dispatch(update: Update, event: Event) -> None:
        for text in await assistant.handle(event):
            await update.effective_message.reply_text(text[: MessageLimit.MAX_TEXT_LENGTH])

    async def on_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await dispatch(update, Start(_user_ref(update)))

    async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await context.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)
        await dispatch(update, Text(_user_ref(update), update.effective_message.text))

    async def on_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        document = update.effective_message.document
        telegram_file = await document.get_file()
        content = bytes(await telegram_file.download_as_bytearray())
        await dispatch(update, File(_user_ref(update), document.file_name or "", content))

    async def on_other(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await dispatch(update, Unsupported(_user_ref(update)))

    async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        # Type only: messages and exception text may contain financial data.
        logger.error("telegram handler failed: %s", type(context.error).__name__)
        if isinstance(update, Update) and update.effective_message is not None:
            await update.effective_message.reply_text(
                "Algo deu errado do meu lado. Tenta de novo em instantes?"
            )

    app = Application.builder().token(token).post_shutdown(on_shutdown).build()
    # Private chats only, and only new messages (edits are ignored).
    base = filters.ChatType.PRIVATE & filters.UpdateType.MESSAGE
    app.add_handler(CommandHandler("start", on_start, filters=base))
    app.add_handler(MessageHandler(base & filters.TEXT, on_text))
    app.add_handler(MessageHandler(base & filters.Document.ALL, on_document))
    app.add_handler(MessageHandler(base, on_other))
    app.add_error_handler(on_error)
    return app


def _user_ref(update: Update) -> UserRef:
    return UserRef("telegram", str(update.effective_user.id))
