#!/usr/bin/env python3
"""
Скрипт для запуска фронтенда в режиме разработки
"""

import subprocess
import sys
import os
from pathlib import Path

def main():
    print("🚀 Запуск фронтенда в режиме разработки...")
    
    # Переходим в директорию фронтенда
    frontend_dir = Path(__file__).parent / "miniapp" / "frontend"
    
    if not frontend_dir.exists():
        print("❌ Директория фронтенда не найдена:", frontend_dir)
        sys.exit(1)
    
    os.chdir(frontend_dir)
    
    try:
        # Проверяем, установлены ли зависимости
        print("📦 Проверка зависимостей...")
        result = subprocess.run(["npm", "list"], capture_output=True, text=True)
        
        if result.returncode != 0:
            print("📦 Установка зависимостей...")
            subprocess.run(["npm", "install"], check=True)
        
        # Запускаем dev сервер
        print("🌐 Запуск dev сервера...")
        print("📍 Фронтенд будет доступен по адресу: http://localhost:5173")
        print("🔄 Нажмите Ctrl+C для остановки")
        
        subprocess.run(["npm", "run", "dev"], check=True)
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка при запуске: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n🛑 Остановка dev сервера...")
        sys.exit(0)

if __name__ == "__main__":
    main()
