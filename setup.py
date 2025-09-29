import os
import sys
import subprocess
from pathlib import Path


def run_command(command, description):
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} - успешно")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - ошибка:")
        print(f"   {e.stderr}")
        return False


def main():
    print("🚀 Настройка RadarBot 3.0")
    print("=" * 50)
    
    if sys.version_info < (3, 8):
        print("❌ Требуется Python 3.8 или выше")
        sys.exit(1)
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}")
    
    if not run_command("pip install -r requirements.txt", "Установка зависимостей"):
        print("❌ Не удалось установить зависимости")
        sys.exit(1)
    
    env_file = Path(".env")
    if not env_file.exists():
        print("📝 Создание файла .env...")
        try:
            with open("env_config.txt", "r", encoding="utf-8") as src:
                content = src.read()
            with open(".env", "w", encoding="utf-8") as dst:
                dst.write(content)
            print("✅ Файл .env создан")
            print("⚠️  ВАЖНО: Отредактируйте .env и заполните T-Bank токены!")
        except Exception as e:
            print(f"❌ Ошибка создания .env: {e}")
            sys.exit(1)
    else:
        print("✅ Файл .env уже существует")
    
    if not run_command("python -c \"from bot.core.db import create_tables; create_tables()\"", "Инициализация базы данных"):
        print("❌ Не удалось инициализировать базу данных")
        sys.exit(1)
    
    print("\n🎉 Настройка завершена!")
    print("\n📋 Следующие шаги:")
    print("1. Отредактируйте файл .env и заполните T-Bank токены")
    print("2. Запустите бота: python main.py")
    print("3. Найдите бота в Telegram и отправьте /start")
    
    print("\n🧪 Для тестирования:")
    print("python -m bot.providers.moex_iss.cli search \"Сбербанк\"")
    print("python tests/test_render_cards.py")


if __name__ == "__main__":
    main()