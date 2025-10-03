#!/usr/bin/env python3
import asyncio
from bot.handlers.invest_analyst import InvestAnalyst

async def final_comprehensive_test():
    analyst = InvestAnalyst()
    
    print('🎯 ФИНАЛЬНЫЙ КОМПЛЕКСНЫЙ ТЕСТ СИСТЕМЫ')
    print('=' * 50)
    
    # Тест 1: Новости
    print('\n📰 Тест новостей...')
    response = await analyst.chat_with_user('test_user', 'Дай новости какие-то хотя бы')
    news_ok = 'новости' in response.lower() and 'ошибка' not in response.lower()
    print(f'✅ Новости: {"РАБОТАЮТ" if news_ok else "НЕ РАБОТАЮТ"}')
    
    # Тест 2: Рыночные данные
    print('\n📊 Тест рыночных данных...')
    response = await analyst.chat_with_user('test_user', 'Какие индексы MOEX?')
    market_ok = 'moex' in response.lower() and 'ошибка' not in response.lower()
    print(f'✅ Индексы: {"РАБОТАЮТ" if market_ok else "НЕ РАБОТАЮТ"}')
    
    # Тест 3: Валюты
    print('\n💱 Тест валют...')
    response = await analyst.chat_with_user('test_user', 'Какие курсы валют?')
    currency_ok = 'доллар' in response.lower() and 'ошибка' not in response.lower()
    print(f'✅ Валюты: {"РАБОТАЮТ" if currency_ok else "НЕ РАБОТАЮТ"}')
    
    # Тест 4: Общий чат
    print('\n💬 Тест общего чата...')
    response = await analyst.chat_with_user('test_user', 'Привет! Как дела?')
    chat_ok = 'ошибка' not in response.lower() and len(response) > 10
    print(f'✅ Чат: {"РАБОТАЕТ" if chat_ok else "НЕ РАБОТАЕТ"}')
    
    print('\n' + '=' * 50)
    all_tests = [news_ok, market_ok, currency_ok, chat_ok]
    passed = sum(all_tests)
    total = len(all_tests)
    
    print(f'📊 РЕЗУЛЬТАТ: {passed}/{total} тестов прошли успешно')
    
    if passed == total:
        print('🎉 ВСЕ ТЕСТЫ ПРОШЛИ УСПЕШНО!')
        print('✅ СИСТЕМА ПОЛНОСТЬЮ РАБОТОСПОСОБНА!')
    else:
        print('⚠️  НЕКОТОРЫЕ ТЕСТЫ НЕ ПРОШЛИ')
    
    return passed == total

if __name__ == "__main__":
    asyncio.run(final_comprehensive_test())
