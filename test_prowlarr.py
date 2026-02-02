#!/usr/bin/env python3
"""Script to test Prowlarr connection and search functionality."""

import asyncio
import sys
from app.config import get_settings
from app.services.prowlarr import ProwlarrService


async def test_prowlarr():
    """Test Prowlarr connection and search."""
    print("🔍 Тестирование подключения к Prowlarr...\n")
    
    try:
        # Load settings
        settings = get_settings()
        print(f"✓ Настройки загружены")
        print(f"  Prowlarr URL: {settings.prowlarr_url}")
        print(f"  API Key: {'*' * 20}{settings.prowlarr_api_key[-8:]}\n")
        
        # Initialize service
        prowlarr = ProwlarrService(
            base_url=settings.prowlarr_url,
            api_key=settings.prowlarr_api_key
        )
        print(f"✓ Сервис инициализирован\n")
        
        # Test search
        test_query = "Interstellar"
        test_year = 2014
        print(f"🔍 Тестовый поиск: '{test_query} {test_year}'")
        print(f"   (ищем раздачи качества 1080p и выше)\n")
        
        torrents = await prowlarr.search_torrents(
            title=test_query,
            year=test_year,
            limit=5
        )
        
        if not torrents:
            print("⚠️  Раздачи не найдены!")
            print("\nВозможные причины:")
            print("  1. В Prowlarr не добавлены индексаторы")
            print("  2. Индексаторы отключены")
            print("  3. Фильм недоступен в качестве 1080p+")
            print("\nОткройте Prowlarr (http://localhost:9696) и добавьте индексаторы.")
            return False
        
        print(f"✓ Найдено раздач: {len(torrents)}\n")
        print("=" * 80)
        
        for i, torrent in enumerate(torrents, 1):
            print(f"\n{i}. {torrent.title[:70]}...")
            print(f"   Источник: {torrent.indexer}")
            print(f"   Разрешение: {torrent.resolution or 'неизвестно'}")
            print(f"   Размер: {torrent.size_gb} GB")
            print(f"   Сиды: {torrent.seeders}")
            print(f"   Magnet: {torrent.magnet_url[:80]}...")
        
        print("\n" + "=" * 80)
        print("\n✅ Тест успешно пройден! Prowlarr работает корректно.")
        return True
        
    except Exception as e:
        print(f"\n❌ Ошибка при тестировании: {e}")
        print("\nПроверьте:")
        print("  1. Prowlarr запущен (docker-compose ps)")
        print("  2. API ключ правильный (Settings → General в Prowlarr)")
        print("  3. URL правильный (должен быть http://prowlarr:9696 для Docker)")
        print("  4. Переменные окружения в .env файле")
        return False


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("Тестирование Prowlarr Integration")
    print("=" * 80 + "\n")
    
    success = asyncio.run(test_prowlarr())
    
    sys.exit(0 if success else 1)
