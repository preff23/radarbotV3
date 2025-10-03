#!/usr/bin/env python3
import asyncio
from bot.services.smart_data_loader import SmartDataLoader
from bot.handlers.invest_analyst import InvestAnalyst

async def test_smart_loader():
    analyst = InvestAnalyst()
    loader = SmartDataLoader(analyst)
    
    # Тестируем запрос новостей
    context = await loader.get_smart_context('А какие новости за сегодня', {})
    print(f'Context keys: {list(context.keys())}')
    if 'news' in context:
        news_items = context['news']
        print(f'News count: {len(news_items)}')
        for item in news_items[:2]:
            print(f'- {item.get("title", "No title")}')

if __name__ == "__main__":
    asyncio.run(test_smart_loader())
