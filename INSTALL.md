# Инструкция по установке и первому запуску

## Первый запуск проекта

### 1. Настройка окружения

Создайте файл `.env` на основе `.env.example`:

```bash
cp .env.example .env
```

Заполните переменные окружения:
- `BOT_TOKEN` - токен бота от @BotFather
- `TMDB_API_KEY` - API ключ от TMDB

### 2. Запуск через Docker Compose

```bash
# Полная очистка и перезапуск (если были проблемы)
docker-compose down -v  # -v удаляет тома (БД будет очищена)
docker-compose build --no-cache
docker-compose up -d

# Просмотр логов
docker-compose logs -f bot
```

### 3. Обычный перезапуск

```bash
docker-compose restart bot
docker-compose logs -f bot
```

## Работа с миграциями

### Применение миграций

Миграции применяются автоматически при запуске контейнера через `entrypoint.sh`.

Для ручного применения:

```bash
# Войти в контейнер
docker-compose exec bot bash

# Применить миграции
alembic upgrade head

# Выйти
exit
```

### Создание новой миграции

После изменения моделей в `app/db/models.py`:

```bash
# Войти в контейнер
docker-compose exec bot bash

# Создать миграцию
alembic revision --autogenerate -m "Описание изменений"

# Выйти
exit

# Перезапустить бота для применения
docker-compose restart bot
```

## Решение проблем

### Ошибка "type roleenum already exists"

Это означает, что в БД есть частично примененные миграции. Решение:

```bash
# Полностью пересоздать БД
docker-compose down -v
docker-compose up -d
```

### Ошибка "relation does not exist"

Миграции не применены. Проверьте логи:

```bash
docker-compose logs bot | grep -i alembic
```

Если миграция не применилась, попробуйте вручную:

```bash
docker-compose exec bot alembic upgrade head
```

### Проблемы с подключением к TMDB

Проверьте, что `TMDB_API_KEY` правильно указан в `.env` файле.
