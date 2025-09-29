from typing import Optional
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    KeyboardButton,
)
from bot.core.db import db_manager
from bot.core.logging import get_logger

logger = get_logger(__name__)

PHONE_REQUEST_TEXT = (
    "Чтобы пользоваться RadarBot, необходимо подтвердить номер телефона.\n"
    "Нажмите кнопку ниже, чтобы поделиться контактом."
)


def _build_phone_keyboard() -> ReplyKeyboardMarkup:
    button = KeyboardButton("📞 Поделиться номером", request_contact=True)
    return ReplyKeyboardMarkup([[button]], resize_keyboard=True, one_time_keyboard=True)


async def send_main_menu(context, chat_id: int, tg_user) -> None:
    welcome_message = f"""
🤖 **Добро пожаловать в RadarBot 3.0!**

Привет, {tg_user.first_name or tg_user.username or 'пользователь'}!

Я помогу вам анализировать инвестиционные портфели:

📸 **OCR анализ** - загрузите фото портфеля
📊 **Рыночные данные** - актуальные цены и изменения
🔍 **Анализ рисков** - оценка без рейтингов Altman
📅 **Календарь выплат** - предстоящие купоны
📰 **Новости** - релевантные новости по эмитентам

Выберите действие в меню ниже:
"""
    keyboard = [
        [InlineKeyboardButton("📊 Портфель", callback_data="portfolio")],
        [InlineKeyboardButton("📈 Анализ", callback_data="analysis")],
        [InlineKeyboardButton("ℹ️ Помощь", callback_data="help")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(
        chat_id=chat_id,
        text=welcome_message,
        parse_mode="Markdown",
        reply_markup=reply_markup,
    )


async def request_phone_number(update, context, *, remind: bool = False) -> None:
    text = PHONE_REQUEST_TEXT
    if remind:
        text = (
            "Нужен ваш номер телефона, чтобы продолжить. "
            "Нажмите кнопку ниже, чтобы поделиться контактом."
        )

    keyboard = _build_phone_keyboard()

    if update.message:
        await update.message.reply_text(text, reply_markup=keyboard)
    elif update.callback_query:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=text,
            reply_markup=keyboard,
        )
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=text,
            reply_markup=keyboard,
        )

    context.user_data["awaiting_phone"] = True


async def handle_contact(update, context) -> None:
    try:
        contact = update.message.contact
        if not contact or not contact.phone_number:
            await update.message.reply_text(
                "Не удалось получить номер телефона. Попробуйте снова."
            )
            await request_phone_number(update, context, remind=True)
            return

        if contact.user_id and contact.user_id != update.effective_user.id:
            await update.message.reply_text(
                "Пожалуйста, поделитесь собственным номером телефона."
            )
            await request_phone_number(update, context, remind=True)
            return

        normalized_phone = db_manager.normalize_phone(contact.phone_number)
        if not normalized_phone:
            await update.message.reply_text(
                "Номер телефона не распознан. Попробуйте снова."
            )
            await request_phone_number(update, context, remind=True)
            return

        tg_user = update.effective_user
        db_user = db_manager.ensure_user(
            normalized_phone,
            telegram_id=tg_user.id,
            username=tg_user.username,
            first_name=tg_user.first_name,
            last_name=tg_user.last_name,
        )

        context.user_data["awaiting_phone"] = False
        context.user_data["user_phone"] = normalized_phone

        await update.message.reply_text(
            "Спасибо! Номер подтверждён.",
            reply_markup=ReplyKeyboardRemove(),
        )

        await send_main_menu(context, update.effective_chat.id, tg_user)

    except Exception as e:
        logger.error(f"Error handling contact: {e}")
        await update.message.reply_text(
            "Не удалось обработать номер телефона. Попробуйте снова."
        )
        await request_phone_number(update, context, remind=True)
