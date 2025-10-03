#!/usr/bin/env python3
from bot.core.db import db_manager
import sqlite3

# Подключаемся к базе напрямую
conn = sqlite3.connect('bot.db')
cursor = conn.cursor()

# Проверяем таблицы
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()

print('Таблицы в базе данных:')
for table in tables:
    print(f'- {table[0]}')

# Проверяем пользователей
try:
    cursor.execute('SELECT id, telegram_id, phone_number, username, first_name FROM users;')
    users = cursor.fetchall()
    
    print(f'\nВсего пользователей в базе: {len(users)}')
    for user in users:
        print(f'ID: {user[0]}, Telegram ID: {user[1]}, Phone: {user[2]}, Username: {user[3]}, Name: {user[4]}')
except Exception as e:
    print(f'Ошибка при получении пользователей: {e}')

conn.close()
