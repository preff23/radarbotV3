#!/usr/bin/env python3
from bot.core.db import create_tables, Base, engine
import sqlite3

print("Создаем таблицы...")
try:
    create_tables()
    print("✅ Таблицы созданы успешно")
except Exception as e:
    print(f"❌ Ошибка при создании таблиц: {e}")

# Проверяем, что таблицы созданы
conn = sqlite3.connect('bot.db')
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()

print(f"\nТаблицы в базе данных ({len(tables)}):")
for table in tables:
    print(f'- {table[0]}')

conn.close()
