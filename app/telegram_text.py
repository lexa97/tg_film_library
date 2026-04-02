"""Лимиты длины текста в Telegram Bot API."""

# https://core.telegram.org/bots/api#sendphoto
TELEGRAM_CAPTION_MAX_LEN = 1024
# https://core.telegram.org/bots/api#sendmessage
TELEGRAM_MESSAGE_MAX_LEN = 4096


def truncate_telegram_caption(text: str, max_len: int = TELEGRAM_CAPTION_MAX_LEN) -> str:
    """Обрезает текст под лимит подписи к медиа (по символам Python str)."""
    if len(text) <= max_len:
        return text
    if max_len <= 1:
        return text[:max_len]
    return text[: max_len - 1] + "…"


def truncate_telegram_message(text: str, max_len: int = TELEGRAM_MESSAGE_MAX_LEN) -> str:
    """Обрезает текст под лимит обычного сообщения."""
    return truncate_telegram_caption(text, max_len=max_len)
