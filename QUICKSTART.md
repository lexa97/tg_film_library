# Быстрый старт

## Запуск через Docker Compose (рекомендуется)

### 1. Проверьте `.env` файл

Убедитесь, что файл `.env` содержит корректные токены:

```env
BOT_TOKEN=dfdfsdfs
TMDB_API_KEY=eyJhbGci...ваш_ключ...
DATABASE_URL=postgresql+asyncpg://tgfilm:tgfilm_secret@10.1.20.24:15432/tg_film_library
```

### 2. Запустите проект

```bash
docker-compose up -d
```

### 3. Проверьте логи

```bash
docker-compose logs -f bot
```

### 4. Остановка

```bash
docker-compose down
```

## Локальный запуск (для разработки)

### 1. Установите зависимости

```bash
pip install -r requirements.txt
```

### 2. Настройте БД

Убедитесь, что PostgreSQL запущен и доступен по адресу из `.env`.

### 3. Примените миграции

```bash
alembic upgrade head
```

Если миграции еще не созданы:

```bash
alembic revision --autogenerate -m "Initial schema"
alembic upgrade head
```

### 4. Запустите бота

```bash
python -m app.main
```

## Тестирование

```bash
# Запуск всех тестов
pytest

# Запуск с покрытием
pytest --cov=app
```

## Проверка кода

```bash
# Проверка линтером
ruff check .

# Автоматическое исправление
ruff check --fix .

# Форматирование
ruff format .
```

## Использование Makefile (Linux/Mac)

```bash
make install   # Установка зависимостей
make test      # Запуск тестов
make lint      # Проверка кода
make format    # Форматирование
make migrate   # Применение миграций
make up        # Запуск Docker Compose
make down      # Остановка Docker Compose
make clean     # Очистка временных файлов
```

## Частые проблемы

### 1. Ошибка подключения к БД

Проверьте, что PostgreSQL запущен:
```bash
docker-compose ps
```

### 2. Ошибка миграций

Если миграции не применяются автоматически в Docker:
```bash
docker-compose exec bot alembic upgrade head
```

### 3. Бот не отвечает

Проверьте логи:
```bash
docker-compose logs -f bot
```

Убедитесь, что `BOT_TOKEN` корректен.

## Первое использование

1. Откройте Telegram и найдите вашего бота
2. Отправьте `/start`
3. Создайте группу
4. Начните добавлять фильмы!

## Разработка

### Добавление новых функций

1. Создайте ветку
2. Внесите изменения
3. Запустите тесты: `pytest`
4. Проверьте код: `ruff check .`
5. Создайте pull request

### Добавление миграций

После изменения моделей:
```bash
alembic revision --autogenerate -m "Описание изменений"
alembic upgrade head
```

## Поддержка

- Документация: `README.md`
- Правила проекта: `rules.md`
- Техническое задание: `task.md`
