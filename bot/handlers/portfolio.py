import asyncio
from typing import Dict, Any, Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from bot.core.db import db_manager
from bot.pipeline.portfolio_ingest_pipeline import ingest_pipeline
from bot.analytics.portfolio_analyzer import portfolio_analyzer
from bot.core.logging import get_logger
from bot.utils.onboarding import request_phone_number

logger = get_logger(__name__)


class PortfolioHandler:
    
    def __init__(self):
        self.db_manager = db_manager
        self.ingest_pipeline = ingest_pipeline
        self.portfolio_analyzer = portfolio_analyzer
    
    def _get_user_phone(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> Optional[str]:
        phone = context.user_data.get('user_phone')
        if phone:
            return phone

        tg_user = update.effective_user
        if not tg_user:
            return None

        user = self.db_manager.get_user_by_telegram_id(tg_user.id)
        if user and getattr(user, 'phone_number', None):
            context.user_data['user_phone'] = user.phone_number
            return user.phone_number
        return None
    
    async def _require_phone(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> Optional[str]:
        phone = self._get_user_phone(update, context)
        if not phone:
            await request_phone_number(update, context, remind=True)
        return phone
    
    async def show_portfolio_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            phone = await self._require_phone(update, context)
            if not phone:
                return

            user = self.db_manager.get_user_by_phone(phone)
            if not user:
                await request_phone_number(update, context, remind=True)
                return

            holdings = self.db_manager.get_user_holdings(user.id, active_only=True)
            holdings_count = len(holdings)

            keyboard = [
                [InlineKeyboardButton("➕ Добавить из фото", callback_data="add_from_photo")],
                [InlineKeyboardButton("➕ Добавить тикер", callback_data="add_ticker")],
                [InlineKeyboardButton("📋 Позиции", callback_data="show_positions")],
                [InlineKeyboardButton("🧹 Очистить", callback_data="clear_portfolio")],
                [InlineKeyboardButton("📊 Анализ", callback_data="run_analysis")]
            ]

            reply_markup = InlineKeyboardMarkup(keyboard)

            message = f"📊 **Портфель**\n\n"
            message += f"Позиций: {holdings_count}\n"
            message += f"Пользователь: {user.first_name or user.username or 'Неизвестно'}\n\n"
            message += "Выберите действие:"

            if update.callback_query:
                await update.callback_query.edit_message_text(
                    message,
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text(
                    message,
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )

        except Exception as e:
            logger.error(f"Failed to show portfolio menu: {e}")
            if update.callback_query:
                await update.callback_query.edit_message_text("Ошибка при загрузке меню портфеля")
            else:
                await update.message.reply_text("Ошибка при загрузке меню портфеля")
    
    async def handle_add_from_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            query = update.callback_query
            await query.answer()
            
            prompt_message = await query.edit_message_text(
                "📸 Отправьте фото портфеля для анализа.\n\n"
                "Поддерживаются скриншоты из приложений брокеров, "
                "выписки и другие изображения с информацией о ценных бумагах."
            )

            context.user_data['waiting_for_photo'] = True
            context.user_data['photo_prompt_message_id'] = prompt_message.message_id
            
        except Exception as e:
            logger.error(f"Failed to handle add from photo: {e}")
            await query.edit_message_text("Ошибка при обработке запроса")
    
    async def handle_add_ticker(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            query = update.callback_query
            await query.answer()
            
            await query.edit_message_text(
                "📝 Введите тикер ценной бумаги для добавления.\n\n"
                "Примеры: SBER, GAZP, LKOH, RU000A105VZ0"
            )
            
            context.user_data['waiting_for_ticker'] = True
            
        except Exception as e:
            logger.error(f"Failed to handle add ticker: {e}")
            await query.edit_message_text("Ошибка при обработке запроса")
    
    async def handle_show_positions(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            query = update.callback_query
            await query.answer()

            phone = await self._require_phone(update, context)
            if not phone:
                return

            user = self.db_manager.get_user_by_phone(phone)

            if not user:
                await query.edit_message_text("Пользователь не найден")
                return

            holdings = self.db_manager.get_user_holdings(user.id, active_only=True)
            
            if not holdings:
                await query.edit_message_text("Портфель пуст")
                return
            
            positions_text = "📋 **Текущие позиции:**\n\n"
            
            for i, holding in enumerate(holdings, 1):
                positions_text += f"{i}. **{holding.normalized_name}**\n"
                if holding.ticker:
                    positions_text += f"   Тикер: {holding.ticker}\n"
                if holding.isin:
                    positions_text += f"   ISIN: {holding.isin}\n"
                if holding.security_type:
                    positions_text += f"   Тип: {holding.security_type}\n"
                if holding.provider:
                    positions_text += f"   Источник: {holding.provider}\n"
                positions_text += "\n"
            
            keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_portfolio")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                positions_text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Failed to show positions: {e}")
            await query.edit_message_text("Ошибка при загрузке позиций")
    
    async def handle_clear_portfolio(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            query = update.callback_query
            await query.answer()
            
            keyboard = [
                [InlineKeyboardButton("✅ Да, очистить", callback_data="confirm_clear")],
                [InlineKeyboardButton("❌ Отмена", callback_data="back_to_portfolio")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "⚠️ **Подтверждение**\n\n"
                "Вы уверены, что хотите очистить весь портфель?\n"
                "Это действие нельзя отменить.",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Failed to handle clear portfolio: {e}")
            await query.edit_message_text("Ошибка при обработке запроса")
    
    async def handle_confirm_clear(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            query = update.callback_query
            await query.answer()

            phone = await self._require_phone(update, context)
            if not phone:
                return

            user = self.db_manager.get_user_by_phone(phone)

            if not user:
                await query.edit_message_text("Пользователь не найден")
                return

            cleared_count = self.db_manager.clear_user_holdings(user.id)
            try:
                self.db_manager.clear_portfolio_meta(user.id)
            except Exception:
                pass
            
            await query.edit_message_text(
                f"✅ Портфель очищен\n\n"
                f"Удалено позиций: {cleared_count}"
            )
            
        except Exception as e:
            logger.error(f"Failed to confirm clear: {e}")
            await query.edit_message_text("Ошибка при очистке портфеля")
    
    async def handle_run_analysis(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            query = update.callback_query
            await query.answer()

            phone = await self._require_phone(update, context)
            if not phone:
                return

            user = self.db_manager.get_user_by_phone(phone)

            if not user:
                await query.edit_message_text("Пользователь не найден")
                return

            await query.edit_message_text("🔄 Выполняется анализ портфеля...")
            
            analysis = await self.portfolio_analyzer.run_analysis(user.id)
            
            if "error" in analysis:
                await query.edit_message_text(f"❌ {analysis['error']}")
                return
            
            await self._send_analysis_results(query, analysis)
            
        except Exception as e:
            logger.error(f"Failed to run analysis: {e}")
            await query.edit_message_text("Ошибка при выполнении анализа")
    
    async def _send_analysis_results(self, query, analysis: Dict[str, Any]):
        try:
            chat = query.message.chat if query.message else query.effective_chat
            
            def clean_text(text):
                text = text.replace('*', '•')
                text = text.replace('[', '(')
                text = text.replace(']', ')')
                text = text.replace('`', "'")
                return text
            
            parts = []
            parts.append(clean_text(analysis["summary"]))
            
            # Убираем отправку таблицы сигналов - пусть ИИ сам решает формат
            if analysis.get("calendar_30d"):
                parts.append(clean_text(analysis["calendar_30d"]))
            if analysis.get("payment_history_summary") and "Нет данных" not in analysis["payment_history_summary"]:
                parts.append(clean_text(analysis["payment_history_summary"]))
            if analysis.get("news_summary") and "Нет новостей" not in analysis["news_summary"]:
                parts.append(clean_text(analysis["news_summary"]))
            if analysis.get("recommendations"):
                parts.append("💡 •Рекомендации•\n\n" + clean_text(analysis["recommendations"]))
            if analysis.get("ai_analysis"):
                parts.append("🤖 •AI-анализ•\n\n" + clean_text(analysis["ai_analysis"]))

            combined = '\n\n'.join(parts)
            max_chunk_size = 3500

            if len(combined) <= max_chunk_size:
                await query.edit_message_text(combined)
            else:
                await query.edit_message_text("📊 •ОТЧЁТ ПО ИНВЕСТИЦИОННОМУ ПОРТФЕЛЮ•")
                paragraphs = combined.split('\n\n')
                current_chunk = ""
                for para in paragraphs:
                    if len(current_chunk + para) > max_chunk_size and current_chunk:
                        await chat.send_message(current_chunk)
                        current_chunk = para
                    else:
                        current_chunk += '\n\n' + para if current_chunk else para
                if current_chunk:
                    await chat.send_message(current_chunk)
 
        except Exception as e:
            logger.error(f"Failed to send analysis results: {e}")
            chat = query.message.chat if query.message else query.effective_chat
            await chat.send_message("Ошибка при отправке результатов анализа")
    
    async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            if not update.message or not update.message.photo:
                await update.message.reply_text(
                    "Не вижу фото в сообщении. Отправьте изображение портфеля или вернитесь в меню /portfolio."
                )
                return

            photo = update.message.photo[-1]
            file = await context.bot.get_file(photo.file_id)
            
            photo_bytes = await file.download_as_bytearray()
            
            processing_msg = await update.message.reply_text("🔄 Обрабатываю фото...")
            
            phone = await self._require_phone(update, context)
            if not phone:
                await processing_msg.edit_text("Нужно подтвердить номер телефона, чтобы обработать фото.")
                return

            user = self.db_manager.get_user_by_phone(phone)

            if not user:
                await processing_msg.edit_text("Пользователь не найден")
                return

            # Обновляем статус только если текст отличается
            if processing_msg.text != "🔄 Обрабатываю фото...":
                await processing_msg.edit_text("🔄 Обрабатываю фото...")
            
            result = await self.ingest_pipeline.ingest_from_photo(user.phone_number, photo_bytes)

            if result.reason == "ok":
                holdings = self.db_manager.get_user_holdings(user.id, active_only=True)

                message = f"✅ **Обработка завершена**\n\n"
                message += f"Добавлено: {result.added}\n"
                message += f"Объединено: {result.merged}\n"
                message += f"Найдено OCR (сырые): {result.raw_detected}\n"
                message += f"После нормализации: {result.normalized}\n"
                message += f"Идентифицировано/разрешено: {result.resolved}\n"
                message += f"Сохранено позиций в базе: {len(holdings)}\n\n"

                if result.positions:
                    message += "**Найденные позиции:**\n"
                    for pos in result.positions:
                        message += f"• {pos['name']}"
                        if pos['ticker']:
                            message += f" ({pos['ticker']})"
                        message += "\n"
                
                await processing_msg.edit_text(message, parse_mode='Markdown')
                
                # Проверяем, нужно ли автоматически запустить анализ
                if context.user_data.get('auto_analysis'):
                    if processing_msg.text != "✅ Фото обработано! Теперь делаю анализ портфеля...":
                        await processing_msg.edit_text("✅ Фото обработано! Теперь делаю анализ портфеля...")
                    
                    # Импортируем analysis_handler для запуска анализа
                    from bot.handlers.analysis import analysis_handler
                    
                    # Запускаем анализ
                    await analysis_handler.handle_analysis_command(update, context)
                    
                    # Сбрасываем флаги только после завершения анализа
                    context.user_data.pop('waiting_for_photo', None)
                    context.user_data.pop('photo_prompt_message_id', None)
                    context.user_data.pop('auto_analysis', None)
                else:
                    # Если не автоматический анализ, оставляем флаг waiting_for_photo для возможности загрузки нескольких фото
                    # Сбрасываем только photo_prompt_message_id
                    context.user_data.pop('photo_prompt_message_id', None)
                    
                    # Добавляем сообщение о возможности загрузить еще фото
                    await update.message.reply_text(
                        "📸 Можете загрузить еще фото или нажмите '📊 Анализ' для запуска анализа портфеля."
                    )
            else:
                error_messages = {
                    "not_portfolio": "❌ На изображении не обнаружен портфель ценных бумаг",
                    "no_valid_securities": "❌ Не найдено валидных ценных бумаг",
                    "error": "❌ Ошибка при обработке изображения"
                }
                
                error_msg = error_messages.get(result.reason, "❌ Неизвестная ошибка")
                await processing_msg.edit_text(error_msg)
                
                # Если это автоматический режим, не сбрасываем флаг waiting_for_photo, чтобы можно было загрузить еще фото
                if not context.user_data.get('auto_analysis'):
                    context.user_data.pop('waiting_for_photo', None)
                context.user_data.pop('photo_prompt_message_id', None)
            
        except Exception as e:
            logger.error(f"Failed to handle photo: {e}", exc_info=True)
            try:
                await update.message.reply_text(f"❌ Ошибка при обработке фото: {str(e)}")
            except Exception as send_error:
                logger.error(f"Failed to send error message: {send_error}")
            finally:
                # Если это автоматический режим, не сбрасываем флаг waiting_for_photo в случае исключения
                if not context.user_data.get('auto_analysis'):
                    context.user_data.pop('waiting_for_photo', None)
                context.user_data.pop('photo_prompt_message_id', None)
    
    async def handle_ticker_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            if not context.user_data.get('waiting_for_ticker'):
                return
            
            context.user_data['waiting_for_ticker'] = False
            
            ticker = update.message.text.strip().upper()
            
            processing_msg = await update.message.reply_text(f"🔄 Добавляю {ticker}...")
            
            phone = await self._require_phone(update, context)
            if not phone:
                await processing_msg.edit_text("Нужно подтвердить номер телефона.")
                return

            user = self.db_manager.get_user_by_phone(phone)

            if not user:
                await processing_msg.edit_text("Пользователь не найден")
                return
            
            result = await self.ingest_pipeline.add_manual_ticker(user.phone_number, ticker)
            
            if result.reason == "ok":
                message = f"✅ **Тикер добавлен**\n\n"
                message += f"Добавлено: {result.added}\n"
                message += f"Объединено: {result.merged}\n"
                
                if result.positions:
                    pos = result.positions[0]
                    message += f"\n**Добавленная позиция:**\n"
                    message += f"• {pos['name']}"
                    if pos['ticker']:
                        message += f" ({pos['ticker']})"
                    if pos['type']:
                        message += f" - {pos['type']}"
                
                await processing_msg.edit_text(message, parse_mode='Markdown')
            else:
                await processing_msg.edit_text(f"❌ Не удалось добавить тикер {ticker}")
            
        except Exception as e:
            logger.error(f"Failed to handle ticker input: {e}")
            await update.message.reply_text("Ошибка при добавлении тикера")
    
    async def handle_back_to_portfolio(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            query = update.callback_query
            await query.answer()
            
            await self.show_portfolio_menu(update, context)
            
        except Exception as e:
            logger.error(f"Failed to handle back to portfolio: {e}")
            await query.edit_message_text("Ошибка при возврате в меню")


portfolio_handler = PortfolioHandler()