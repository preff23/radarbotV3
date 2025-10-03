# 🔍 Руководство по Мониторингу и Тестированию

## 🚀 Быстрый Старт

### 1. Запуск Бота с Мониторингом
```bash
python start_bot.py
```
Этот скрипт запускает:
- 🤖 Основного бота
- 📊 Систему мониторинга в реальном времени
- 🔧 Все необходимые сервисы

### 2. Запуск Только Мониторинга
```bash
python monitor_system.py monitor
```

### 3. Быстрая Проверка Системы
```bash
python monitor_system.py check
```

### 4. Просмотр Метрик
```bash
python monitor_system.py metrics
```

### 5. Запуск Тестов
```bash
python run_tests.py
```

---

## 📊 API Endpoints для Мониторинга

### Health Checks
- **GET** `/api/health/` - Общий статус системы
- **GET** `/api/health/summary` - Краткая сводка
- **GET** `/api/health/components/{name}` - Статус компонента
- **GET** `/api/health/metrics` - Метрики системы
- **POST** `/api/health/check` - Принудительная проверка

### Cache Management
- **GET** `/api/cache/ocr/stats` - Статистика OCR кэша
- **DELETE** `/api/cache/ocr/clear` - Очистка кэша
- **POST** `/api/cache/ocr/cleanup` - Очистка истекших записей
- **GET** `/api/cache/errors/stats` - Статистика ошибок
- **DELETE** `/api/cache/errors/reset` - Сброс счетчиков ошибок

### CorpBonds API
- **GET** `/api/corpbonds/bond/{isin}` - Данные облигации
- **POST** `/api/corpbonds/bonds` - Данные нескольких облигаций
- **GET** `/api/corpbonds/health` - Проверка работоспособности

---

## 🔧 Компоненты Мониторинга

### 1. Database Health
- ✅ Проверка подключения к БД
- ⏱️ Измерение времени ответа
- 📊 Количество пользователей

### 2. Cache Health
- 📈 Использование кэша OCR
- 🎯 Hit rate (процент попаданий)
- 🗑️ Очистка истекших записей

### 3. Error Monitoring
- 🚨 Количество ошибок по категориям
- ⚠️ Уровни серьезности
- 📊 Статистика по времени

### 4. Memory Health
- 💾 Использование памяти
- 📈 Тренды потребления
- ⚠️ Предупреждения о переполнении

### 5. External APIs
- 🌐 Доступность MOEX API
- 🏦 Доступность T-Bank API
- ⏱️ Время ответа внешних сервисов

---

## 🧪 Тестирование

### Автоматические Тесты
```bash
python run_tests.py
```

Тесты проверяют:
- ✅ OCR Cache (кэширование, статистика)
- ✅ Error Handler (обработка ошибок)
- ✅ Health Monitor (мониторинг компонентов)
- ✅ CorpBonds Integration (парсинг облигаций)
- ✅ Smart Data Loader (умная загрузка данных)

### Ручное Тестирование

#### Тест OCR Cache
```python
from bot.utils.ocr_cache import ocr_cache

# Статистика кэша
stats = ocr_cache.get_stats()
print(f"Cache size: {stats['cache_size']}")
print(f"Hit rate: {stats['hit_rate']}%")

# Очистка кэша
ocr_cache.clear()
```

#### Тест Error Handler
```python
from bot.core.error_handler import handle_error, ErrorSeverity, ErrorCategory

# Обработка ошибки
error_info = handle_error(
    ValueError("Test error"),
    severity=ErrorSeverity.LOW,
    category=ErrorCategory.BUSINESS_LOGIC
)
```

#### Тест Health Monitor
```python
from bot.core.health_monitor import health_monitor

# Проверка здоровья системы
health = await health_monitor.get_system_health()
print(f"Status: {health.overall_status}")
```

---

## 📈 Метрики и Алерты

### Критические Алерты
- ❌ База данных недоступна
- ❌ Кэш переполнен (>95%)
- ❌ Слишком много критических ошибок (>10)
- ❌ Внешние API недоступны

### Предупреждения
- ⚠️ База данных медленно отвечает (>5s)
- ⚠️ Кэш почти полон (>90%)
- ⚠️ Повышенный уровень ошибок
- ⚠️ Высокое использование памяти

### Нормальные Показатели
- ✅ База данных: <5s ответ
- ✅ Кэш: <90% заполнения
- ✅ Ошибки: <5 критических
- ✅ Память: <1GB

---

## 🛠️ Устранение Проблем

### Проблема: Бот не запускается
```bash
# Проверяем логи
tail -f bot_run.log

# Проверяем конфигурацию
python -c "from bot.core.config import config; print(config.validate())"

# Запускаем тесты
python run_tests.py
```

### Проблема: Медленная работа
```bash
# Проверяем кэш
curl http://localhost:8000/api/cache/ocr/stats

# Очищаем кэш
curl -X DELETE http://localhost:8000/api/cache/ocr/clear

# Проверяем метрики
python monitor_system.py metrics
```

### Проблема: Много ошибок
```bash
# Смотрим статистику ошибок
curl http://localhost:8000/api/cache/errors/stats

# Сбрасываем счетчики
curl -X DELETE http://localhost:8000/api/cache/errors/reset

# Проверяем здоровье системы
python monitor_system.py check
```

---

## 🔄 Автоматизация

### Cron Jobs для Мониторинга
```bash
# Добавить в crontab
# Проверка каждые 5 минут
*/5 * * * * cd /path/to/radar3.0 && python monitor_system.py check >> monitoring.log 2>&1

# Очистка кэша каждый час
0 * * * * cd /path/to/radar3.0 && curl -X POST http://localhost:8000/api/cache/ocr/cleanup
```

### Systemd Service
```ini
[Unit]
Description=RadarBot 3.0 with Monitoring
After=network.target

[Service]
Type=simple
User=radarbot
WorkingDirectory=/path/to/radar3.0
ExecStart=/usr/bin/python3 start_bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

---

## 📱 Уведомления

### Telegram Уведомления
```python
# Добавить в health_monitor.py
async def send_telegram_alert(message: str):
    # Отправка уведомления в Telegram
    pass
```

### Email Уведомления
```python
# Добавить в health_monitor.py
async def send_email_alert(message: str):
    # Отправка email уведомления
    pass
```

---

## 🎯 Рекомендации

1. **Регулярно проверяйте** статус системы
2. **Мониторьте метрики** кэша и ошибок
3. **Очищайте кэш** при необходимости
4. **Следите за логами** для выявления проблем
5. **Настройте алерты** для критических состояний

---

## 🆘 Поддержка

При возникновении проблем:
1. Запустите `python run_tests.py`
2. Проверьте `python monitor_system.py check`
3. Посмотрите логи в `bot_run.log`
4. Проверьте API endpoints мониторинга
