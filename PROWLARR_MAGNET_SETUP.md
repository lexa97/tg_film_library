# Настройка Prowlarr для получения Magnet-ссылок

## Проблема

По умолчанию Prowlarr может возвращать только `downloadUrl` (ссылки на торрент-файлы), а не прямые magnet-ссылки.

## Решение

### Шаг 1: Включите Advanced Settings

1. Откройте Prowlarr: http://localhost:9696
2. Перейдите в **Settings** (⚙️ Настройки)
3. В правом верхнем углу найдите кнопку **Show Advanced** и включите её

### Шаг 2: Настройте глобальные параметры индексаторов

1. В **Settings → General**
2. Найдите секцию **Indexers**
3. Включите опции (если есть):
   - ✅ **Prefer Magnet Links** (Предпочитать magnet-ссылки)

### Шаг 3: Настройте каждый индексатор

Для каждого добавленного индексатора (например, RuTracker):

1. Перейдите в **Indexers** (на главной странице)
2. Нажмите на индексатор для редактирования
3. **Важно:** Найдите параметры:
   
   **Для RuTracker.org:**
   - **Download Mode**: Выберите **Magnet** (вместо Torrent)
   - Или **Strip Size from Magnet Link**: отключите (если есть)
   
   **Общие параметры:**
   - **Enable RSS**: ✅ включено
   - **Enable Automatic Search**: ✅ включено
   - **Enable Interactive Search**: ✅ включено

4. **Test** → **Save**

### Шаг 4: Проверьте возможности индексатора

1. В списке индексаторов нажмите на кнопку **Test All**
2. Убедитесь, что все индексаторы зелёные
3. Попробуйте сделать тестовый поиск прямо в Prowlarr:
   - **Search** → введите название фильма
   - В результатах должна быть кнопка с magnet-значком 🧲
   - Нажмите на неё - должна открыться magnet-ссылка

### Шаг 5: Специфичные настройки для популярных трекеров

#### RuTracker.org

1. Откройте настройки индексатора RuTracker
2. Прокрутите вниз до секции **Specific Settings**
3. Найдите **Download Link Type** или **Torrent Link Type**:
   - Выберите **Magnet Link** (вместо Torrent File)
4. Сохраните

#### RuTor

Обычно работает "из коробки" с magnet-ссылками.

#### Kinozal

Может не поддерживать magnet-ссылки напрямую. Проверьте настройки.

### Шаг 6: Альтернативный метод - FlareSolverr (если нужен)

Некоторые трекеры требуют решения CloudFlare защиты. Если у вас проблемы с доступом:

1. Добавьте FlareSolverr в docker-compose.yml:
   ```yaml
   flaresolverr:
     image: ghcr.io/flaresolverr/flaresolverr:latest
     container_name: flaresolverr
     ports:
       - "8191:8191"
     networks:
       - film_library_network
   ```

2. В Prowlarr → Settings → Indexers:
   - **FlareSolverr URL**: http://flaresolverr:8191
   - **Tags**: добавьте тег для индексаторов, которым нужен FlareSolverr

### Проверка через API

Вы можете проверить, что возвращает API:

```bash
curl "http://localhost:9696/api/v1/search?query=Interstellar&type=search&categories=2000" \
  -H "X-Api-Key: ВАШ_API_КЛЮЧ" | jq '.[] | {title: .title, magnetUrl: .magnetUrl, downloadUrl: .downloadUrl}'
```

Если `magnetUrl` пустой - значит индексатор настроен на торрент-файлы.

## Что делать, если magnet-ссылки всё равно не работают

### Вариант 1: Используйте индексаторы с поддержкой magnet

Некоторые трекеры лучше поддерживают magnet:
- **The Pirate Bay** (публичный)
- **1337x** (публичный)
- **RuTor** (публичный, русский)

Добавьте их в Prowlarr как дополнительные источники.

### Вариант 2: Проверьте версию Prowlarr

Убедитесь, что используете последнюю версию:

```bash
docker-compose pull prowlarr
docker-compose up -d prowlarr
```

### Вариант 3: Проверьте логи Prowlarr

```bash
docker-compose logs prowlarr | tail -50
```

Ищите ошибки или предупреждения.

## Итоговая проверка

После настройки:

1. Перезапустите бота: `docker-compose restart bot`
2. Найдите фильм в Telegram боте
3. Нажмите "🧲 Magnet"
4. Проверьте логи бота - должно быть:
   ```
   Found magnet link for: ...
   ```

## Полезные ссылки

- [Prowlarr Wiki - Indexers](https://wiki.servarr.com/prowlarr/indexers)
- [Prowlarr Discord](https://discord.gg/prowlarr)

---

**Важно:** Если конкретный трекер не поддерживает magnet-ссылки через API, бот всё равно будет работать - просто будет отдавать ссылку на скачивание торрент-файла через Prowlarr.
