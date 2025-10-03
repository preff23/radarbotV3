import asyncio
import os
import signal
import sys
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from bot.core.config import config
from bot.core.logging import setup_logging, get_logger
from bot.core.db import create_tables, db_manager
from bot.handlers.portfolio import portfolio_handler
from bot.handlers.analysis import analysis_handler
from bot.handlers.invest_analyst import invest_analyst
from bot.utils.onboarding import send_main_menu, request_phone_number, handle_contact
from bot.core.error_handler import handle_error, ErrorSeverity, ErrorCategory, ErrorContext, safe_execute_async

setup_logging()
logger = get_logger(__name__)

# Глобальная переменная для приложения
application = None

def signal_handler(signum, frame):
    """Обработчик сигналов для graceful shutdown"""
    logger.info(f"Received signal {signum}, shutting down gracefully...")
    if application:
        try:
            # Останавливаем polling
            asyncio.create_task(application.stop())
            asyncio.create_task(application.shutdown())
            logger.info("Application stopped gracefully")
        except Exception as e:
            logger.error(f"Error during graceful shutdown: {e}")
    sys.exit(0)

async def graceful_shutdown():
    """Graceful shutdown приложения"""
    logger.info("Starting graceful shutdown...")
    try:
        if application:
            await application.stop()
            await application.shutdown()
        logger.info("Graceful shutdown completed")
    except Exception as e:
        logger.error(f"Error during graceful shutdown: {e}")


async def start_command(update, context):
    error_context = ErrorContext(
        user_id=str(update.effective_user.id) if update.effective_user else None,
        operation="start_command"
    )
    
    try:
        user = update.effective_user

        db_user = db_manager.get_user_by_telegram_id(user.id)

        if not db_user or not getattr(db_user, "phone_number", None):
            await request_phone_number(update, context)
            return

        context.user_data['awaiting_phone'] = False
        await send_main_menu(context, update.effective_chat.id, user)

    except Exception as e:
        error_info = handle_error(
            e,
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.TELEGRAM,
            context=error_context
        )
        
        try:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Произошла ошибка. Попробуйте позже.",
            )
        except Exception as send_error:
            handle_error(
                send_error,
                severity=ErrorSeverity.MEDIUM,
                category=ErrorCategory.TELEGRAM,
                context=error_context
            )


async def help_command(update, context):
    help_text = """
📖 **Справка по RadarBot 3.0**

**Основные команды:**
/start - Главное меню
/help - Эта справка
/portfolio - Управление портфелем
/analysis - Анализ портфеля
/app - Открыть веб-приложение

**Как использовать:**

1. **Добавьте позиции:**
   - 📸 Загрузите фото портфеля
   - 📝 Введите тикер вручную

2. **Запустите анализ:**
   - Нажмите "📊 Анализ"
   - Получите подробный отчёт

**Поддерживаемые форматы:**
- Скриншоты из приложений брокеров
- Выписки по портфелю
- Изображения с информацией о ценных бумагах

**Источники данных:**
- T-Bank Invest API (основной)
- MOEX ISS API (резервный)
- RBC и Smart-Lab новости

**Безопасность:**
- Каждый пользователь видит только свой портфель
- Данные изолированы и защищены
- Никаких рейтингов Altman

Если у вас есть вопросы, обратитесь к администратору.
"""
    
    await update.message.reply_text(help_text, parse_mode='Markdown')


async def app_command(update, context):
    try:
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        
        message = """
📱 **Веб-приложение Radar**

Откройте удобный веб-интерфейс для работы с портфелем:

✨ **Возможности:**
• 📸 Загрузка фото портфеля
• 📊 Красивый анализ данных  
• 📋 Удобный просмотр позиций
• 🔍 Детальная статистика

Нажмите кнопку ниже для открытия:
"""
        
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("📱 Открыть приложение", web_app={"url": "http://localhost:5001"})
        ]])
        
        await update.message.reply_text(
            message,
            parse_mode='Markdown',
            reply_markup=keyboard
        )
        
    except Exception as e:
        logger.error(f"Error in app command: {e}")
        await update.message.reply_text("Произошла ошибка. Попробуйте позже.")


async def callback_handler(update, context):
    try:
        query = update.callback_query
        if not query:
            logger.error("No callback query in update")
            return
            
        await query.answer()
        
        data = query.data

        if context.user_data.get('awaiting_phone'):
            await request_phone_number(update, context, remind=True)
            return

        if data == "portfolio":
            await portfolio_handler.show_portfolio_menu(update, context)
        elif data == "analysis":
            await analysis_handler.handle_analysis_command(update, context)
        elif data == "help":
            await help_command(update, context)
        elif data == "add_from_photo":
            await portfolio_handler.handle_add_from_photo(update, context)
        elif data == "add_ticker":
            await portfolio_handler.handle_add_ticker(update, context)
        elif data == "show_positions":
            await portfolio_handler.handle_show_positions(update, context)
        elif data == "clear_portfolio":
            await portfolio_handler.handle_clear_portfolio(update, context)
        elif data == "confirm_clear":
            await portfolio_handler.handle_confirm_clear(update, context)
        elif data == "run_analysis":
            await portfolio_handler.handle_run_analysis(update, context)
        elif data == "back_to_portfolio":
            await portfolio_handler.handle_back_to_portfolio(update, context)
        else:
            await query.edit_message_text("Неизвестная команда")
            
    except Exception as e:
        logger.error(f"Error in callback handler: {e}")
        if query:
            await query.edit_message_text("Произошла ошибка. Попробуйте позже.")
        else:
            logger.error("Cannot send error message: no query available")


async def message_handler(update, context):
    error_context = ErrorContext(
        user_id=str(update.effective_user.id) if update.effective_user else None,
        operation="message_handler"
    )
    
    try:
        if update.message and update.message.contact:
            await handle_contact(update, context)
            return

        if context.user_data.get('awaiting_phone'):
            await request_phone_number(update, context, remind=True)
            return

        phone_number = context.user_data.get('user_phone')

        if not phone_number:
            user = db_manager.get_user_by_telegram_id(update.effective_user.id)
            if user and getattr(user, 'phone_number', None):
                phone_number = user.phone_number
                context.user_data['user_phone'] = phone_number
            else:
                await request_phone_number(update, context, remind=True)
                return

        if context.user_data.get('waiting_for_photo'):
            # Если пользователь написал текстовое сообщение, выходим из режима ожидания фото
            if update.message and update.message.text:
                context.user_data.pop('waiting_for_photo', None)
                # Продолжаем обработку как обычное текстовое сообщение
            else:
                if update.message:
                    await update.message.reply_text(
                        "Ожидаю фото портфеля. Отправьте изображение или напишите текстовое сообщение для выхода из режима загрузки фото."
                    )
                return

        if context.user_data.get('waiting_for_ticker'):
            # Если пользователь написал текстовое сообщение, выходим из режима ожидания тикера
            if update.message and update.message.text:
                context.user_data.pop('waiting_for_ticker', None)
                # Продолжаем обработку как обычное текстовое сообщение
            else:
                await portfolio_handler.handle_ticker_input(update, context)
                return

        message_text = update.message.text

        # Показываем анимацию "Генерирую сообщение"
        from bot.utils.typing_animation import show_typing_animation
        animation = await show_typing_animation(context.bot, update.effective_chat.id, "Генерирую сообщение")

        try:
            response = await invest_analyst.chat_with_user(phone_number, message_text)
            
            # Останавливаем анимацию и отправляем ответ
            await animation.stop()
            await update.message.reply_text(response, parse_mode='Markdown')
            
        except Exception as e:
            # Останавливаем анимацию в случае ошибки
            await animation.stop()
            handle_error(
                e,
                severity=ErrorSeverity.HIGH,
                category=ErrorCategory.BUSINESS_LOGIC,
                context=error_context
            )
            await update.message.reply_text("Извините, произошла ошибка при обработке сообщения. Попробуйте позже.")

    except Exception as e:
        error_info = handle_error(
            e,
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.TELEGRAM,
            context=error_context
        )
        await update.message.reply_text("Извините, произошла ошибка. Попробуйте позже.")


async def photo_handler(update, context):
    try:
        if context.user_data.get('waiting_for_photo'):
            await portfolio_handler.handle_photo(update, context)
        else:
            prompt_message_id = context.user_data.get('photo_prompt_message_id')
            if prompt_message_id:
                reply_to = update.message.reply_to_message
                if reply_to and reply_to.message_id == prompt_message_id:
                    await portfolio_handler.handle_photo(update, context)
                    return

            if context.user_data.get('awaiting_phone'):
                await request_phone_number(update, context, remind=True)
            else:
                await update.message.reply_text(
                    "Для анализа фото портфеля сначала выберите 'Добавить из фото' в меню портфеля."
                )

    except Exception as e:
        logger.error(f"Error in photo handler: {e}")
        await update.message.reply_text("Произошла ошибка при обработке фото.")


def main():
    global application
    
    try:
        config.validate()
        
        create_tables()
        logger.info("Database tables created successfully")
        
        # Регистрируем обработчики сигналов
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        application = Application.builder().token(config.telegram_bot_token).build()
        
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("app", app_command))
        application.add_handler(CommandHandler("portfolio", portfolio_handler.show_portfolio_menu))
        application.add_handler(CommandHandler("analysis", analysis_handler.handle_analysis_command))
        
        application.add_handler(CallbackQueryHandler(callback_handler))
        application.add_handler(MessageHandler(filters.CONTACT, handle_contact))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
        application.add_handler(MessageHandler(filters.PHOTO, photo_handler))
        
        logger.info("Starting RadarBot 3.0...")
        
        # Запускаем приложение с обработкой ошибок
        try:
            application.run_polling(
                allowed_updates=["message", "callback_query"],
                drop_pending_updates=True,  # Игнорируем старые обновления
                close_loop=False  # Не закрываем event loop при остановке
            )
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt, shutting down...")
        except Exception as poll_err:
            logger.error(f"Polling stopped: {poll_err}")
            raise
        
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        raise
    finally:
        # Graceful shutdown при выходе
        if application:
            try:
                asyncio.run(graceful_shutdown())
            except Exception as shutdown_err:
                logger.error(f"Error during final shutdown: {shutdown_err}")


if __name__ == "__main__":
    main()