# Tron Energy Rental Bot

Telegram-бот для автоматизации аренды ресурса Energy в сети Tron. Репозиторий содержит только код бота и вспомогательных воркеров без базы данных и файлов с секретами.

## Стек

- Python 3.11+
- aiogram 2.x
- SQLite (структура БД создаётся при первом запуске)
- Docker / Docker Compose (опционально)

## Запуск

1. Создать файл `.env` по образцу переменных в `app/models/config.py` (токен бота, API-ключ TronGrid и т.п.).
2. Установить зависимости:

```bash
pip install -r requirements.txt
```

3. Запустить бота:

```bash
python -m app.run
```

Или через Docker Compose:

```bash
docker compose up --build
```

В репозиторий **не** входят реальные значения токенов, приватные ключи и файлы базы данных.
