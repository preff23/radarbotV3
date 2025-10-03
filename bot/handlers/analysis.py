from telegram import Update
from telegram.ext import ContextTypes
from bot.analytics.portfolio_analyzer import portfolio_analyzer
from bot.core.db import db_manager
from bot.core.logging import get_logger

logger = get_logger(__name__)


class AnalysisHandler:
    
    def __init__(self):
        self.portfolio_analyzer = portfolio_analyzer
        self.db_manager = db_manager
    
    async def handle_analysis_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            phone = context.user_data.get('user_phone')
            if not phone:
                from bot.utils.onboarding import request_phone_number
                await request_phone_number(update, context, remind=True)
                return

            user = self.db_manager.get_user_by_phone(phone)
            if not user:
                await update.effective_chat.send_message("Пользователь не найден")
                return
            
            message = update.message
            if not message and update.callback_query:
                message = update.callback_query.message
            
            if not message:
                logger.error("No message object available for analysis command")
                return
            
            loading_msg = await message.reply_text("🔄 Выполняется анализ портфеля...")
            
            analysis = await self.portfolio_analyzer.run_analysis(user.id)
            
            if "error" in analysis:
                await loading_msg.edit_text(f"❌ {analysis['error']}")
                return
            
            await self._send_analysis_results(loading_msg, analysis)
            
        except Exception as e:
            logger.error(f"Failed to handle analysis command: {e}")
            try:
                message = update.message or (update.callback_query.message if update.callback_query else None)
                if message:
                    await message.reply_text("❌ Произошла ошибка. Попробуйте позже.")
            except:
                pass
    
    
    async def _send_analysis_results(self, message, analysis: dict):
        try:
            logger.info("Starting to send analysis results")
            
            chat = message.chat
            logger.info(f"Got chat: {chat}")
            
            def clean_text(text):
                text = text.replace('*', '•')
                text = text.replace('[', '(')
                text = text.replace(']', ')')
                text = text.replace('`', "'")
                return text
            
            logger.info("Sending summary")
            summary_text = analysis["summary"]
            summary_text = clean_text(summary_text)
            
            max_chunk_size = 1000
            if len(summary_text) > max_chunk_size:
                logger.info(f"Summary too long ({len(summary_text)} chars), splitting into chunks")
                await message.edit_text("📊 •ОТЧЁТ ПО ИНВЕСТИЦИОННОМУ ПОРТФЕЛЮ•")
                paragraphs = summary_text.split('\n\n')
                current_chunk = ""
                for para in paragraphs:
                    if len(current_chunk + para) > max_chunk_size and current_chunk:
                        await chat.send_message(current_chunk)
                        current_chunk = para
                    else:
                        current_chunk += '\n\n' + para if current_chunk else para
                if current_chunk:
                    await chat.send_message(current_chunk)
            else:
                await message.edit_text(summary_text)
            
            if analysis["signals_table"]:
                logger.info("Sending signals table")
                signals_text = "📊 •Таблица сигналов•\n\n" + analysis["signals_table"]
                signals_text = clean_text(signals_text)
                
                if len(signals_text) > max_chunk_size:
                    logger.info(f"Signals table too long ({len(signals_text)} chars), splitting into chunks")
                    await chat.send_message("📊 •Таблица сигналов•")
                    clean_signals_table = clean_text(analysis["signals_table"])
                    cards = clean_signals_table.split('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
                    current_chunk = ""
                    for i, card in enumerate(cards):
                        if i == 0:
                            continue
                        card_text = '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━' + card
                        if len(current_chunk + card_text) > max_chunk_size and current_chunk:
                            await chat.send_message(current_chunk)
                            current_chunk = card_text
                        else:
                            current_chunk += card_text
                    if current_chunk:
                        await chat.send_message(current_chunk)
                else:
                    await chat.send_message(signals_text)
            
            if analysis.get("calendar_30d"):
                calendar_text = analysis["calendar_30d"]
                calendar_text = clean_text(calendar_text)
                
                if len(calendar_text) > max_chunk_size:
                    await chat.send_message("📅 •КАЛЕНДАРЬ ВЫПЛАТ (30 дней)•")
                    lines = calendar_text.split('\n')
                    current_chunk = ""
                    for line in lines:
                        if len(current_chunk + line + '\n') > max_chunk_size and current_chunk:
                            await chat.send_message(current_chunk)
                            current_chunk = line + '\n'
                        else:
                            current_chunk += line + '\n'
                    if current_chunk:
                        await chat.send_message(current_chunk)
                else:
                    await chat.send_message(calendar_text)
            
            if analysis.get("payment_history_summary") and "Нет данных" not in analysis["payment_history_summary"]:
                payment_history_text = clean_text(analysis["payment_history_summary"])
                
                if len(payment_history_text) > max_chunk_size:
                    await chat.send_message("📊 •ИСТОРИЯ ВЫПЛАТ•")
                    lines = payment_history_text.split('\n')
                    current_chunk = ""
                    for line in lines:
                        if len(current_chunk + line + '\n') > max_chunk_size and current_chunk:
                            await chat.send_message(current_chunk)
                            current_chunk = line + '\n'
                        else:
                            current_chunk += line + '\n'
                    if current_chunk:
                        await chat.send_message(current_chunk)
                else:
                    await chat.send_message(payment_history_text)
            
            if analysis.get("news_summary") and "Нет новостей" not in analysis["news_summary"]:
                news_text = clean_text(analysis["news_summary"])
                
                if len(news_text) > max_chunk_size:
                    paragraphs = news_text.split('\n\n')
                    current_chunk = ""
                    for para in paragraphs:
                        if len(current_chunk + para) > max_chunk_size and current_chunk:
                            await chat.send_message(current_chunk)
                            current_chunk = para
                        else:
                            current_chunk += '\n\n' + para if current_chunk else para
                    if current_chunk:
                        await chat.send_message(current_chunk)
                else:
                    await chat.send_message(news_text)
            
            if analysis["recommendations"]:
                recommendations_text = "💡 •Рекомендации•\n\n" + analysis["recommendations"]
                recommendations_text = clean_text(recommendations_text)
                
                if len(recommendations_text) > max_chunk_size:
                    await chat.send_message("💡 •Рекомендации•")
                    paragraphs = analysis["recommendations"].split('\n\n')
                    current_chunk = ""
                    for para in paragraphs:
                        if len(current_chunk + para) > max_chunk_size and current_chunk:
                            await chat.send_message(current_chunk)
                            current_chunk = para
                        else:
                            current_chunk += '\n\n' + para if current_chunk else para
                    if current_chunk:
                        await chat.send_message(current_chunk)
                else:
                    await chat.send_message(recommendations_text)
            
            if "ai_analysis" in analysis and analysis["ai_analysis"]:
                logger.info("Sending AI analysis")
                ai_text = analysis["ai_analysis"]
                ai_text = clean_text(ai_text)
                
                if len(ai_text) > max_chunk_size:
                    logger.info(f"AI analysis too long ({len(ai_text)} chars), splitting into chunks")
                    await chat.send_message("🤖 AI Анализ (v14.4)")
                    
                    paragraphs = ai_text.split('\n\n')
                    current_chunk = ""
                    
                    for para in paragraphs:
                        if len(current_chunk + para) > max_chunk_size and current_chunk:
                            await chat.send_message(current_chunk)
                            current_chunk = para
                        else:
                            current_chunk += '\n\n' + para if current_chunk else para
                    
                    if current_chunk:
                        await chat.send_message(current_chunk)
                else:
                    # Проверяем длину сообщения
                    full_text = f"🤖 AI Анализ (v14.4)\n\n{ai_text}"
                    if len(full_text) > 4096:
                        # Разбиваем на части
                        max_chunk_size = 4000
                        chunks = []
                        current_chunk = "🤖 AI Анализ (v14.4)\n\n"
                        
                        paragraphs = ai_text.split('\n\n')
                        for para in paragraphs:
                            if len(current_chunk + para) > max_chunk_size and current_chunk:
                                chunks.append(current_chunk)
                                current_chunk = para
                            else:
                                current_chunk += '\n\n' + para if current_chunk else para
                        
                        if current_chunk:
                            chunks.append(current_chunk)
                        
                        for i, chunk in enumerate(chunks):
                            if i > 0:
                                chunk = f"🤖 AI Анализ (v14.4) - часть {i+1}\n\n{chunk}"
                            await chat.send_message(chunk)
                    else:
                        await chat.send_message(full_text)
            
            logger.info("Analysis results sent successfully")
            
        except Exception as e:
            logger.error(f"Failed to send analysis results: {e}", exc_info=True)
            logger.error(f"AI text length: {len(ai_text) if ai_text else 'None'}")
            logger.error(f"AI text preview: {ai_text[:200] if ai_text else 'None'}")
            try:
                await message.chat.send_message("Ошибка при отправке результатов анализа")
            except Exception as send_error:
                logger.error(f"Failed to send error message: {send_error}")
    
    async def _send_detailed_analysis(self, update: Update, user_id: int):
        """Отправляет детальный анализ проблемных эмитентов"""
        try:
            from bot.handlers.invest_analyst import invest_analyst
            
            # Получаем номер телефона пользователя
            user = self.db_manager.get_user_by_id(user_id)
            if not user or not getattr(user, 'phone_number', None):
                logger.warning(f"No phone number for user {user_id}")
                return
            
            # Запускаем детальный анализ
            detailed_analysis = await invest_analyst._run_detailed_analysis(user.phone_number)
            
            # Отправляем результат
            chat = update.effective_chat
            if detailed_analysis and "❌" not in detailed_analysis:
                await chat.send_message(detailed_analysis)
            else:
                logger.warning(f"Detailed analysis failed or empty for user {user_id}")
                
        except Exception as e:
            logger.error(f"Failed to send detailed analysis: {e}")


analysis_handler = AnalysisHandler()