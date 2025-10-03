# Интеграция парсера corpbonds.ru

## Обзор

Парсер corpbonds.ru интегрирован в проект для автоматического извлечения данных об облигациях и их использования в AI анализе портфеля и мини-приложении.

## Компоненты

### 1. Парсер (`bot/utils/corpbonds_parser_v2.py`)

Основной парсер для извлечения данных с сайта corpbonds.ru:

- **Метод**: `get_bond_info(isin)` - получение данных по ISIN
- **Функциональность**: 
  - Парсинг основной информации об облигации
  - Извлечение финансовых данных эмитента
  - Получение рейтингов
  - Анализ событий (купонные выплаты)
  - Информация об эмитенте
  - Рыночные данные

### 2. Сервис (`bot/services/corpbonds_service.py`)

Сервисный слой для работы с парсером:

- **Кэширование**: Избежание повторных запросов
- **Параллельная обработка**: Получение данных для нескольких облигаций одновременно
- **Форматирование**: Подготовка данных для AI анализа
- **Обработка ошибок**: Graceful handling ошибок

**Основные методы:**
- `get_bond_data(isin)` - данные одной облигации
- `get_multiple_bonds_data(isins)` - данные нескольких облигаций
- `extract_bond_summary(data)` - краткая сводка
- `format_for_ai_analysis(data)` - форматирование для AI

### 3. API Endpoints (`bot/api/corpbonds_endpoints.py`)

REST API для мини-приложения:

- `GET /api/corpbonds/bond/{isin}` - данные облигации
- `POST /api/corpbonds/bonds` - данные нескольких облигаций
- `GET /api/corpbonds/bond/{isin}/summary` - краткая сводка
- `GET /api/corpbonds/bonds/summaries` - сводки нескольких облигаций
- `DELETE /api/corpbonds/cache` - очистка кэша
- `GET /api/corpbonds/health` - проверка работоспособности

### 4. Интеграция в AI анализ (`bot/analytics/portfolio_analyzer.py`)

Автоматическое получение данных corpbonds.ru для облигаций в портфеле:

- Извлечение ISIN облигаций из портфеля
- Параллельное получение данных с corpbonds.ru
- Форматирование данных для передачи в AI
- Интеграция в промпт анализа

## Использование

### В AI анализе портфеля

Данные автоматически загружаются при анализе портфеля:

```python
# В PortfolioAnalyzer._generate_ai_analysis()
bond_isins = [snapshot.isin for snapshot in snapshots if snapshot.isin and snapshot.isin.startswith('RU')]
corpbonds_data = await corpbonds_service.get_multiple_bonds_data(bond_isins)
corpbonds_block = corpbonds_service.format_for_ai_analysis(corpbonds_data)
```

### В мини-приложении

```javascript
// Получение данных облигации
const response = await fetch('/api/corpbonds/bond/RU000A10BNF8');
const bondData = await response.json();

// Получение данных нескольких облигаций
const response = await fetch('/api/corpbonds/bonds/summaries?isins=RU000A10BNF8,RU000A1082X0');
const bondsData = await response.json();
```

### Программное использование

```python
from bot.services.corpbonds_service import corpbonds_service

# Получение данных одной облигации
bond_data = await corpbonds_service.get_bond_data("RU000A10BNF8")

# Получение данных нескольких облигаций
bonds_data = await corpbonds_service.get_multiple_bonds_data(["RU000A10BNF8", "RU000A1082X0"])

# Краткая сводка
summary = corpbonds_service.extract_bond_summary(bond_data)
```

## Структура данных

### Полные данные облигации

```json
{
  "url": "https://corpbonds.ru/bond/RU000A10BNF8",
  "basic_info": {
    "name": "РусГидро",
    "isin": "RU000A10BNF8",
    "nominal": 1000.0,
    "currency": "RUB",
    "coupon_rate": 17.35,
    "maturity_date": "11.08.2027",
    "payment_frequency": "Месяц и меньше"
  },
  "financial_data": {},
  "ratings": [
    {"agency": "АКРА", "rating": "AAA"},
    {"agency": "Эксперт РА", "rating": "AAA"}
  ],
  "events": [
    {"type": "coupon", "date": "20.10.2025", "amount": "14.26"}
  ],
  "issuer_info": {
    "name": "РусГидро",
    "sector": "Энергетика"
  },
  "market_data": {
    "price": 104.78,
    "yield": 15.39
  }
}
```

### Краткая сводка

```json
{
  "isin": "RU000A10BNF8",
  "name": "РусГидро",
  "url": "https://corpbonds.ru/bond/RU000A10BNF8",
  "nominal": 1000.0,
  "currency": "RUB",
  "coupon_rate": 17.35,
  "current_price": 104.78,
  "yield": 15.39,
  "ratings": {
    "АКРА": "AAA",
    "Эксперт РА": "AAA"
  },
  "issuer_name": "РусГидро",
  "sector": "Энергетика",
  "upcoming_coupons": [
    {"date": "20.10.2025", "amount": "14.26"}
  ]
}
```

## Производительность

- **Кэширование**: Избежание повторных запросов к corpbonds.ru
- **Параллельная обработка**: Одновременное получение данных для нескольких облигаций
- **Обработка ошибок**: Graceful handling недоступности сайта
- **Таймауты**: Предотвращение зависания при медленных запросах

## Мониторинг

### Логирование

Все операции логируются с уровнем INFO/ERROR:

```python
logger.info(f"Fetching data for bond {isin} from corpbonds.ru")
logger.info(f"Successfully cached data for {isin}")
logger.error(f"Error parsing bond {isin}: {e}")
```

### Health Check

Endpoint `/api/corpbonds/health` проверяет работоспособность:

```json
{
  "status": "healthy",
  "message": "Сервис corpbonds.ru работает корректно",
  "test_bond": "RU000A10BNF8"
}
```

## Ограничения

1. **Зависимость от сайта**: Парсер зависит от доступности и структуры corpbonds.ru
2. **Rate limiting**: Возможны ограничения на количество запросов
3. **Изменения структуры**: Парсер может сломаться при изменении HTML структуры сайта
4. **Только российские облигации**: Парсер работает только с ISIN, начинающимися с "RU"

## Тестирование

Запуск тестов интеграции:

```bash
python3 test_corpbonds_integration.py
```

Тестирование парсера:

```bash
python3 test_corpbonds_v2.py
```

## Развертывание

1. Убедитесь, что все зависимости установлены
2. Проверьте доступность corpbonds.ru
3. Запустите тесты интеграции
4. Перезапустите сервисы

## Поддержка

При проблемах с парсером:

1. Проверьте доступность corpbonds.ru
2. Очистите кэш: `DELETE /api/corpbonds/cache`
3. Проверьте логи на ошибки парсинга
4. Запустите health check: `GET /api/corpbonds/health`
