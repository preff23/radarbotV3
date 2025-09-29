import asyncio
import openai
from typing import Optional, Dict, Any
from bot.core.config import config
from bot.core.logging import setup_logging

setup_logging()

class BondSectorDetector:
    
    def __init__(self):
        self.openai_client = openai.OpenAI(
            base_url="https://neuroapi.host/v1",
            api_key=config.openai_api_key
        )
        self.sector_cache = {}
    
    async def detect_sector(self, bond_name: str, ticker: str = "", isin: str = "") -> Optional[str]:
        """Detect bond sector using AI analysis of the bond name.

        Args:
            bond_name: Full name of the bond
            ticker: Bond ticker (optional)
            isin: Bond ISIN (optional)

        Returns:
            Detected sector name or None
        """
        if not bond_name:
            return None
        
        cache_key = f"{bond_name}_{ticker}_{isin}"
        if cache_key in self.sector_cache:
            return self.sector_cache[cache_key]
        
        try:
            context = f"Название облигации: {bond_name}"
            if ticker:
                context += f"\nТикер: {ticker}"
            if isin:
                context += f"\nISIN: {isin}"
            
            prompt = f"""Проанализируй название облигации и определи отрасль эмитента.

Контекст:
{context}

Определи отрасль эмитента на основе названия облигации. Используй следующие категории:

1. Банки - банковские организации, кредитные организации
2. Лизинг - лизинговые компании
3. Энергетика - нефтегазовые компании, электроэнергетика
4. Транспорт - транспортные компании, логистика
5. Телекоммуникации - операторы связи, IT-компании
6. Строительство - строительные компании, недвижимость
7. Металлургия - металлургические компании, горнодобыча
8. Химия - химические компании, фармацевтика
9. Сельское хозяйство - агропромышленные компании
10. Розничная торговля - торговые сети, ритейл
11. Пищевая промышленность - производители продуктов питания
12. Машиностроение - машиностроительные компании
13. Финансы - финансовые компании (не банки), МФК
14. Государственные - государственные облигации, муниципальные
15. Другое - если не подходит ни одна категория

Ответь ТОЛЬКО названием отрасли из списка выше. Если не уверен, выбери наиболее подходящую категорию."""

            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Ты эксперт по российским облигациям и отраслям экономики."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=50,
                temperature=0.1
            )
            
            sector = response.choices[0].message.content.strip()
            
            valid_sectors = [
                "Банки", "Лизинг", "Энергетика", "Транспорт", "Телекоммуникации",
                "Строительство", "Металлургия", "Химия", "Сельское хозяйство",
                "Розничная торговля", "Пищевая промышленность", "Машиностроение",
                "Финансы", "Государственные", "Другое"
            ]
            
            if sector in valid_sectors:
                self.sector_cache[cache_key] = sector
                return sector
            else:
                sector_lower = sector.lower()
                for valid_sector in valid_sectors:
                    if valid_sector.lower() in sector_lower or sector_lower in valid_sector.lower():
                        self.sector_cache[cache_key] = valid_sector
                        return valid_sector
                
                self.sector_cache[cache_key] = "Другое"
                return "Другое"
                
        except Exception as e:
            print(f"Ошибка AI определения отрасли для '{bond_name}': {e}")
            return None
    
    def get_sector_from_cache(self, bond_name: str, ticker: str = "", isin: str = "") -> Optional[str]:
        cache_key = f"{bond_name}_{ticker}_{isin}"
        return self.sector_cache.get(cache_key)

bond_sector_detector = BondSectorDetector()

async def test_sector_detection():
    print("🔍 Тестирование AI определения отраслей облигаций...")
    
    test_bonds = [
        ("ПИР БО-02-001P", "RU000A108C17", "RU000A108C17"),
        ("РДВ ТЕХНОЛОДЖИ 1P1", "RU000A10ANT1", "RU000A10ANT1"),
        ("РЕГИНСПЕЦТРАНС-01", "RU000A109NM3", "RU000A109NM3"),
        ("Сибирский КХП 001P-04", "RU000A10BRN3", "RU000A10BRN3"),
        ("ТД РКС-Сочи выпуск 1", "RU000A101PV6", "RU000A101PV6"),
        ("УПТК-65 001Р-01", "RU000A10C9Z9", "RU000A10C9Z9"),
        ("МФК ВЭББАНКИР 06", "RU000A1082K7", "RU000A1082K7"),
        ("Оил Ресурс 001P-02", "RU000A10C8H9", "RU000A10C8H9"),
        ("Пионер-Лизинг БО6", "RU000A1090H6", "RU000A1090H6"),
        ("Интерскол КЛС БО-03", "RU000A10ATB6", "RU000A10ATB6"),
        ("ЛК Роделен БО 001Р-04", "RU000A105SK4", "RU000A105SK4"),
    ]
    
    for name, ticker, isin in test_bonds:
        print(f"\n🔍 Облигация: {name}")
        print(f"   Тикер: {ticker}")
        
        try:
            sector = await bond_sector_detector.detect_sector(name, ticker, isin)
            print(f"   ✅ Определенная отрасль: {sector}")
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")
    
    print(f"\n📊 Тестирование завершено!")

if __name__ == "__main__":
    asyncio.run(test_sector_detection())