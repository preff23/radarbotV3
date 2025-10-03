#!/usr/bin/env python3
"""
Скрипт для запуска бота с мониторингом
"""

import asyncio
import sys
import os
import signal
import subprocess
from pathlib import Path

# Добавляем корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent))

from bot.core.logging import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)


def print_banner():
    """Печатает баннер запуска"""
    print("🤖 RADARBOT 3.0 - ЗАПУСК С МОНИТОРИНГОМ")
    print("=" * 50)
    print("🚀 Запуск бота...")
    print("📊 Мониторинг активен")
    print("⏹️ Нажмите Ctrl+C для остановки")
    print("=" * 50)


def start_monitoring():
    """Запускает мониторинг в отдельном процессе"""
    try:
        # Запускаем мониторинг в фоне
        monitor_process = subprocess.Popen([
            sys.executable, "monitor_system.py", "monitor"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        logger.info(f"Мониторинг запущен с PID: {monitor_process.pid}")
        return monitor_process
    except Exception as e:
        logger.error(f"Ошибка запуска мониторинга: {e}")
        return None


def start_bot():
    """Запускает основного бота"""
    try:
        # Запускаем бота
        bot_process = subprocess.Popen([
            sys.executable, "main.py"
        ])
        
        logger.info(f"Бот запущен с PID: {bot_process.pid}")
        return bot_process
    except Exception as e:
        logger.error(f"Ошибка запуска бота: {e}")
        return None


def cleanup_processes(processes):
    """Останавливает все процессы"""
    print("\n🛑 Остановка процессов...")
    
    for name, process in processes.items():
        if process and process.poll() is None:
            try:
                process.terminate()
                process.wait(timeout=5)
                print(f"✅ {name} остановлен")
            except subprocess.TimeoutExpired:
                process.kill()
                print(f"🔪 {name} принудительно остановлен")
            except Exception as e:
                print(f"❌ Ошибка остановки {name}: {e}")


def signal_handler(signum, frame):
    """Обработчик сигналов для graceful shutdown"""
    print(f"\n📡 Получен сигнал {signum}, останавливаем процессы...")
    sys.exit(0)


def main():
    """Главная функция"""
    print_banner()
    
    # Регистрируем обработчики сигналов
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    processes = {}
    
    try:
        # Запускаем мониторинг
        print("📊 Запуск мониторинга...")
        monitor_process = start_monitoring()
        if monitor_process:
            processes["Мониторинг"] = monitor_process
            print("✅ Мониторинг запущен")
        else:
            print("❌ Не удалось запустить мониторинг")
        
        # Небольшая задержка
        import time
        time.sleep(2)
        
        # Запускаем бота
        print("🤖 Запуск бота...")
        bot_process = start_bot()
        if bot_process:
            processes["Бот"] = bot_process
            print("✅ Бот запущен")
        else:
            print("❌ Не удалось запустить бота")
            cleanup_processes(processes)
            return 1
        
        print("\n🎉 ВСЕ СИСТЕМЫ ЗАПУЩЕНЫ!")
        print("=" * 50)
        print("📊 Мониторинг: http://localhost:8000/api/health/")
        print("🔧 Кэш: http://localhost:8000/api/cache/ocr/stats")
        print("📈 Метрики: http://localhost:8000/api/health/metrics")
        print("=" * 50)
        print("⏹️ Нажмите Ctrl+C для остановки")
        
        # Ждем завершения процессов
        while True:
            # Проверяем статус процессов
            for name, process in processes.items():
                if process and process.poll() is not None:
                    print(f"⚠️ {name} завершился с кодом {process.returncode}")
                    if name == "Бот":
                        print("❌ Бот остановлен, завершаем работу")
                        cleanup_processes(processes)
                        return process.returncode
            
            time.sleep(1)
    
    except KeyboardInterrupt:
        print("\n⏹️ Получен сигнал остановки")
    except Exception as e:
        print(f"\n💥 Критическая ошибка: {e}")
        logger.error(f"Critical error in start_bot: {e}")
    finally:
        cleanup_processes(processes)
        print("👋 Все процессы остановлены")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
