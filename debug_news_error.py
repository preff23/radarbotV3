#!/usr/bin/env python3
import asyncio
import traceback
from bot.handlers.invest_analyst import InvestAnalyst

async def test_invest_news():
    try:
        analyst = InvestAnalyst()
        response = await analyst.chat_with_user('test_user', 'Дай новости какие-то хотя бы')
        print('Response:', response)
    except Exception as e:
        print('Error:', e)
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_invest_news())
