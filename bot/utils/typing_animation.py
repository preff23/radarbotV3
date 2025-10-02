"""
Утилита для анимации "Генерирую сообщение" в Telegram
"""

import asyncio
from typing import Optional
from telegram import Bot, Message
from bot.core.logging import get_logger

logger = get_logger(__name__)


class TypingAnimation:
    """Класс для управления анимацией печати в Telegram"""
    
    def __init__(self, bot: Bot, chat_id: int):
        self.bot = bot
        self.chat_id = chat_id
        self.message: Optional[Message] = None
        self.is_running = False
        self.task: Optional[asyncio.Task] = None
    
    async def start(self, base_text: str = "Генерирую сообщение") -> None:
        """Запускает анимацию печати"""
        if self.is_running:
            return
        
        try:
            self.is_running = True
            self.message = await self.bot.send_message(
                chat_id=self.chat_id,
                text=base_text
            )
            
            # Запускаем анимацию в фоне
            self.task = asyncio.create_task(self._animate(base_text))
            
        except Exception as e:
            logger.error(f"Error starting typing animation: {e}")
            self.is_running = False
    
    async def stop(self) -> None:
        """Останавливает анимацию печати"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        
        # Удаляем сообщение с анимацией
        if self.message:
            try:
                await self.message.delete()
            except Exception as e:
                logger.error(f"Error deleting typing animation message: {e}")
            finally:
                self.message = None
    
    async def _animate(self, base_text: str) -> None:
        """Анимация точек"""
        dots = ["", ".", "..", "...", "....", "....."]
        dot_index = 0
        
        while self.is_running:
            try:
                if self.message:
                    text = f"{base_text}{dots[dot_index]}"
                    await self.message.edit_text(text)
                    
                    dot_index = (dot_index + 1) % len(dots)
                    await asyncio.sleep(0.5)
                else:
                    break
                    
            except Exception as e:
                logger.error(f"Error in typing animation: {e}")
                break


async def show_typing_animation(bot: Bot, chat_id: int, base_text: str = "Генерирую сообщение") -> TypingAnimation:
    """
    Показывает анимацию печати и возвращает объект для управления
    
    Args:
        bot: Telegram Bot объект
        chat_id: ID чата
        base_text: Базовый текст для анимации
    
    Returns:
        TypingAnimation: Объект для управления анимацией
    """
    animation = TypingAnimation(bot, chat_id)
    await animation.start(base_text)
    return animation


async def with_typing_animation(bot: Bot, chat_id: int, base_text: str = "Генерирую сообщение"):
    """
    Контекстный менеджер для анимации печати
    
    Usage:
        async with with_typing_animation(bot, chat_id, "Анализирую портфель"):
            # Ваш код здесь
            pass
    """
    animation = TypingAnimation(bot, chat_id)
    await animation.start(base_text)
    
    try:
        yield animation
    finally:
        await animation.stop()
