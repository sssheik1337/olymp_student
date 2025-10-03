# Olympiad Bot

Телеграм-бот для управления олимпиадами и подготовкой школьников.

## Быстрый старт

1. Установите зависимости проекта:
   ```bash
   pip install -e olympiad-bot
   ```
2. Создайте базу данных PostgreSQL и пользователя с доступом к ней.
3. Скопируйте файл `.env.example` в `.env` и заполните значения:
   ```bash
   cp olympiad-bot/.env.example olympiad-bot/.env
   ```
4. Запустите миграции Alembic:
   ```bash
   cd olympiad-bot
   alembic upgrade head
   ```
5. Запустите бота в режиме polling:
   ```bash
   python -m src.bot.app
   ```

> ⚠️ Поддержка webhook и интеграция через AMVERA/NGROK будут добавлены позднее.

## Переменные окружения

Основные параметры берутся из файла `.env`:

- `BOT_TOKEN` — токен Telegram-бота.
- `ADMIN_IDS` — список Telegram ID администраторов.
- `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` — настройки доступа к PostgreSQL.
- `PAY_PROVIDER`, `PAY_RETURN_URL` — параметры плательщика (заглушка).
- `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI` — данные для интеграции с Google Calendar (заглушка).

После запуска бот работает в режиме long polling. Все дополнительные интеграции (webhook, внешние туннели) будут настроены на последующих этапах.
