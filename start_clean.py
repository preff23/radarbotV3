#!/usr/bin/env python3
"""
Чистый запуск бота без конфликтов
"""

import os
import sys
import signal
import subprocess
import time
from pathlib import Path

def kill_existing_processes():
    """Убивает все существующие процессы бота"""
    print("🔄 Остановка существующих процессов...")
    
    # Команды для поиска и остановки процессов
    kill_commands = [
        "pkill -f 'python.*main.py'",
        "pkill -f 'monitor_system.py'", 
        "pkill -f 'miniapp/backend/main.py'"
    ]
    
    for cmd in kill_commands:
        try:
            os.system(cmd)
        except:
            pass
    
    time.sleep(2)
    print("✅ Существующие процессы остановлены")

def start_bot():
    """Запускает основного бота"""
    print("🤖 Запуск основного бота...")
    
    try:
        # Запускаем бота в фоне
        process = subprocess.Popen([
            sys.executable, "main.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        print(f"✅ Бот запущен с PID: {process.pid}")
        return process
    except Exception as e:
        print(f"❌ Ошибка запуска бота: {e}")
        return None

def start_api():
    """Запускает API сервер"""
    print("🌐 Запуск API сервера...")
    
    try:
        # Запускаем API в фоне
        process = subprocess.Popen([
            sys.executable, "miniapp/backend/main.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        print(f"✅ API сервер запущен с PID: {process.pid}")
        return process
    except Exception as e:
        print(f"❌ Ошибка запуска API: {e}")
        return None

def signal_handler(signum, frame):
    """Обработчик сигналов"""
    print(f"\n🛑 Получен сигнал {signum}, останавливаем процессы...")
    kill_existing_processes()
    sys.exit(0)

def main():
    """Главная функция"""
    print("🚀 RADARBOT 3.0 - ЧИСТЫЙ ЗАПУСК")
    print("=" * 50)
    
    # Регистрируем обработчики сигналов
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Останавливаем существующие процессы
    kill_existing_processes()
    
    # Запускаем процессы
    processes = []
    
    # Запускаем бота
    bot_process = start_bot()
    if bot_process:
        processes.append(("Бот", bot_process))
    
    # Небольшая задержка
    time.sleep(3)
    
    # Запускаем API
    api_process = start_api()
    if api_process:
        processes.append(("API", api_process))
    
    if not processes:
        print("❌ Не удалось запустить ни одного процесса")
        return 1
    
    print("\n🎉 СИСТЕМА ЗАПУЩЕНА!")
    print("=" * 50)
    print("🤖 Бот: активен")
    print("🌐 API: http://localhost:8000")
    print("📊 Мониторинг: http://localhost:8000/api/health/")
    print("=" * 50)
    print("⏹️ Нажмите Ctrl+C для остановки")
    
    try:
        # Ждем завершения процессов
        while True:
            for name, process in processes:
                if process.poll() is not None:
                    print(f"⚠️ {name} завершился с кодом {process.returncode}")
                    if name == "Бот":
                        print("❌ Бот остановлен, завершаем работу")
                        kill_existing_processes()
                        return process.returncode
            
            time.sleep(1)
    
    except KeyboardInterrupt:
        print("\n⏹️ Получен сигнал остановки")
    finally:
        kill_existing_processes()
        print("👋 Все процессы остановлены")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
