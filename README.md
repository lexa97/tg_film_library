# Telegram Film Library Bot

Telegram-бот вайбкодился для решения простой задачи - ведения совместного списка фильмов, которые надо посмотреть вечерком на диване. Вдвоём или компанией. 


## Возможности

- 👥 Создание логических групп внутри бота
- 🔍 Поиск фильмов и сериалов через TMDB API
- 📋 Общий список «к просмотру» для группы
- ✅ Отметка фильмов как просмотренных
- 🔔 Уведомления участникам группы о новых фильмах и просмотрах
- 🧲 Поиск торрент-раздач через Prowlarr (720p и выше)
- 📥 Получение magnet-ссылок или торрент-файлов для скачивания

## Технологический стек

- Python 3.10-3.14 (рекомендуется 3.13)
- aiogram 3.24+
- PostgreSQL 14+
- SQLAlchemy 2.0 (async)
- TMDB API
- Prowlarr (для поиска торрентов)
- Docker & Docker Compose

## Структура проекта

```
app/
  handlers/       # Обработчики Telegram
  keyboards/      # Inline-клавиатуры
  db/             # Модели БД и репозитории
  middlewares/    # Middleware
  services/       # Бизнес-логика
  states/         # FSM-состояния
  utils/          # Утилиты
initdb.py         # Инициализация БД
tests/            # Тесты
```

## Быстрый старт

### Локальный запуск (без Docker)

1. Клонируйте репозиторий:
```bash
git clone <repo-url>
cd tg_film_library
```

2. Создайте виртуальное окружение и установите зависимости:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows

# Для работы бота
pip install -r requirements.txt

# Для разработки (включает тесты и линтер)
pip install -r requirements-dev.txt
```

3. Настройте `.env` файл:
```env
BOT_TOKEN=your_telegram_bot_token
TMDB_API_KEY=your_tmdb_api_key
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/tg_film_library
```

4. Инициализируйте БД:
```bash
python initdb.py
```

5. Запустите бота:
```bash
python -m app.main
```

### Запуск через Docker Compose

1. Убедитесь, что у вас установлены Docker и Docker Compose.

2. Настройте `.env` файл (BOT_TOKEN, TMDB_API_KEY, PROWLARR_API_KEY):
```env
BOT_TOKEN=your_telegram_bot_token
TMDB_API_KEY=your_tmdb_api_key
PROWLARR_URL=http://prowlarr:9696
PROWLARR_API_KEY=your_prowlarr_api_key
```

3. Запустите проект:
```bash
docker-compose up -d
```

4. Настройте Prowlarr:
   - Откройте http://localhost:9696 в браузере
   - Пройдите первоначальную настройку
   - В Settings → General скопируйте API Key
   - Добавьте API Key в `.env` файл как `PROWLARR_API_KEY`
   - В Settings → Indexers добавьте нужные индексаторы (например, RuTracker, RuTor и т.д.)
   - Перезапустите бота: `docker-compose restart bot`

4. Просмотр логов:
```bash
docker-compose logs -f bot
```

5. Остановка:
```bash
docker-compose down
```

## Изменение структуры БД

После изменения моделей в `app/db/models.py`:

1. Остановите бота
2. При следующем запуске `initdb.py` создаст новые таблицы автоматически
3. **Важно:** Скрипт не удаляет и не изменяет существующие таблицы/колонки

Для полного пересоздания БД:
```bash
docker-compose down -v  # Удаляет том с БД
docker-compose up -d    # Создает чистую БД
```

## Тестирование

Для запуска тестов установите dev-зависимости:
```bash
pip install -r requirements-dev.txt
```

Запуск тестов:
```bash
pytest
```

Запуск с покрытием:
```bash
pytest --cov=app --cov-report=html
```

## Проверка кода

Проверка линтером (требует requirements-dev.txt):
```bash
ruff check .
```

Автоматическое исправление:
```bash
ruff check --fix .
```

## Использование бота

1. **Начало работы:** отправьте `/start` боту
2. **Создание группы:** нажмите кнопку "Создать группу" и введите название
3. **Добавление участников:** администратор отправляет боту контакт пользователя (Поделиться контактом)
4. **Поиск фильмов:** просто отправьте название фильма боту
5. **Добавление в список:** нажмите "Подтвердить" у найденного фильма
6. **Просмотр списка:** команда `/list` или кнопка "Мой список"
7. **Отметка просмотренным:** выберите фильм из списка и нажмите "Просмотрено"
8. **Поиск и скачивание торрентов:** нажмите кнопку "📥 Скачать" под описанием фильма
9. **Выбор раздачи:** выберите нужную раздачу из списка - она автоматически отправится в ваш торрент-клиент

## Архитектура

Проект следует принципу разделения ответственности (SRP):

- **Handlers** — приём обновлений от Telegram
- **Services** — бизнес-логика
- **Repositories** — доступ к БД
- **Keyboards** — сборка клавиатур

Вся бизнес-логика реализована через классы. Функции используются только как утилиты.

## Лицензия

MIT

## Автор

Разработано с использованием лучших практик Python и aiogram 3.x
