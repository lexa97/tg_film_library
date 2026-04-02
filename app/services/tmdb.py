"""TMDB film search provider."""

import logging
from typing import Optional, Any
import httpx

from app.services.base import BaseFilmSearchProvider
from app.services.dto import FilmSearchResult
from app.config import get_settings


logger = logging.getLogger(__name__)


class TMDBFilmSearch(BaseFilmSearchProvider):
    """TMDB API film search provider."""
    
    BASE_URL = "https://api.themoviedb.org/3"
    IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"
    
    def __init__(self):
        """Initialize TMDB search provider."""
        settings = get_settings()
        self.api_key = settings.tmdb_api_key
        self.proxy_url = settings.proxy_url
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "accept": "application/json"
        }
        
        if self.proxy_url:
            logger.info(f"TMDB will use proxy: {self.proxy_url}")
    
    async def search(
        self, 
        query: str, 
        language: str = "ru"
    ) -> Optional[list[FilmSearchResult]]:
        """Search films in TMDB.
        
        Args:
            query: Search query
            language: Language code
            
        Returns:
            List of up to 5 search results, or None if API error occurred
        """
        try:
            logger.debug(f"TMDB search request: query={query}, language={language}")
            logger.debug(f"TMDB URL: {self.BASE_URL}/search/multi")
            
            # Создаем клиент с прокси если указан
            client_kwargs = {"timeout": 10.0}
            if self.proxy_url:
                client_kwargs["proxy"] = self.proxy_url
            
            async with httpx.AsyncClient(**client_kwargs) as client:
                response = await client.get(
                    f"{self.BASE_URL}/search/multi",
                    params={
                        "query": query,
                        "language": language,
                        "include_adult": "false"
                    },
                    headers=self.headers
                )
                
                logger.debug(f"TMDB response status: {response.status_code}")
                response.raise_for_status()
                data = response.json()
                
                results = []
                for item in data.get("results", [])[:5]:
                    # Only process movies and TV shows
                    if item.get("media_type") not in ["movie", "tv"]:
                        continue
                    
                    result = self._parse_search_result(item)
                    if result:
                        results.append(result)
                
                logger.info(f"TMDB search found {len(results)} results")
                return results
                
        except httpx.ConnectError as e:
            logger.error(f"TMDB connection error (check network/DNS): {e}")
            return None
        except httpx.TimeoutException as e:
            logger.error(f"TMDB timeout error: {e}")
            return None
        except httpx.HTTPStatusError as e:
            logger.error(f"TMDB HTTP error {e.response.status_code}: {e.response.text}")
            return None
        except httpx.HTTPError as e:
            logger.error(f"TMDB HTTP error: {type(e).__name__}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in TMDB search: {type(e).__name__}: {e}", exc_info=True)
            return None
    
    async def get_details(
        self,
        external_id: str,
        media_type: str
    ) -> Optional[FilmSearchResult]:
        """Get film details from TMDB.
        
        Args:
            external_id: TMDB ID
            media_type: 'movie' or 'tv'
            
        Returns:
            Film details or None
        """
        try:
            endpoint = f"{self.BASE_URL}/{media_type}/{external_id}"
            logger.debug(f"TMDB get details: {endpoint}")
            
            # Создаем клиент с прокси если указан
            client_kwargs = {"timeout": 10.0}
            if self.proxy_url:
                client_kwargs["proxy"] = self.proxy_url
            
            async with httpx.AsyncClient(**client_kwargs) as client:
                response = await client.get(
                    endpoint,
                    params={
                        "language": "ru",
                        # Подтягиваем кредиты, чтобы вытащить режиссёра
                        "append_to_response": "credits",
                    },
                    headers=self.headers,
                )
                
                logger.debug(f"TMDB details response status: {response.status_code}")
                response.raise_for_status()
                data = response.json()
                
                return self._parse_details(data, media_type)
                
        except httpx.ConnectError as e:
            logger.error(f"TMDB connection error (check network/DNS): {e}")
            return None
        except httpx.TimeoutException as e:
            logger.error(f"TMDB timeout error: {e}")
            return None
        except httpx.HTTPStatusError as e:
            logger.error(f"TMDB HTTP error {e.response.status_code}: {e.response.text}")
            return None
        except httpx.HTTPError as e:
            logger.error(f"TMDB HTTP error: {type(e).__name__}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in TMDB get details: {type(e).__name__}: {e}", exc_info=True)
            return None

    async def _fetch_recommendations_page(
        self,
        external_id: str,
        media_type: str,
    ) -> Optional[list[tuple[str, str]]] | str:
        """
        Один запрос к /movie|tv/{id}/recommendations.

        Returns:
            список (в т.ч. пустой) при 200;
            "not_found" при 404 (часто неверный movie vs tv);
            None при прочей ошибке.
        """
        endpoint = f"{self.BASE_URL}/{media_type}/{external_id}/recommendations"
        try:
            client_kwargs = {"timeout": 10.0}
            if self.proxy_url:
                client_kwargs["proxy"] = self.proxy_url
            async with httpx.AsyncClient(**client_kwargs) as client:
                response = await client.get(
                    endpoint,
                    params={
                        "api_key": self.api_key,
                        "language": "ru-RU",
                        "page": 1,
                    },
                    headers=self.headers,
                )
                if response.status_code == 404:
                    return "not_found"
                response.raise_for_status()
                data = response.json()
            out: list[tuple[str, str]] = []
            for item in data.get("results") or []:
                rid = item.get("id")
                if rid is not None:
                    out.append((str(rid), media_type))
            return out
        except httpx.HTTPStatusError as e:
            logger.error(
                "TMDB fetch_recommendations HTTP %s для %s: %s",
                e.response.status_code,
                endpoint,
                (e.response.text or "")[:400],
            )
            return None
        except httpx.HTTPError as e:
            logger.error("TMDB fetch_recommendations HTTP error: %s", e)
            return None
        except Exception as e:
            logger.error("TMDB fetch_recommendations: %s", e, exc_info=True)
            return None

    async def fetch_recommendations(
        self,
        external_id: str,
        media_type: str,
    ) -> Optional[list[tuple[str, str]]]:
        """Первая страница recommendations; при 404 пробуем противоположный тип (tv↔movie)."""
        first = await self._fetch_recommendations_page(external_id, media_type)
        if isinstance(first, list):
            return first
        if first != "not_found":
            return None
        alt = "tv" if media_type == "movie" else "movie"
        second = await self._fetch_recommendations_page(external_id, alt)
        if isinstance(second, list):
            logger.info(
                "TMDB recommendations: external_id=%s в БД как %s, ответ TMDB по эндпоинту %s",
                external_id,
                media_type,
                alt,
            )
            return second
        return None

    def _parse_search_result(self, item: dict[str, Any]) -> Optional[FilmSearchResult]:
        """Parse search result item.
        
        Args:
            item: TMDB API result item
            
        Returns:
            Parsed result or None
        """
        try:
            media_type = item.get("media_type")
            
            # Get title based on media type
            if media_type == "movie":
                title = item.get("title", "")
                original_title = item.get("original_title")
                release_date = item.get("release_date", "")
            else:  # tv
                title = item.get("name", "")
                original_title = item.get("original_name")
                release_date = item.get("first_air_date", "")
            
            # Extract year from release date
            year = None
            if release_date:
                try:
                    year = int(release_date.split("-")[0])
                except (ValueError, IndexError):
                    pass
            
            # Get poster URL
            poster_path = item.get("poster_path")
            poster_url = f"{self.IMAGE_BASE_URL}{poster_path}" if poster_path else None
            
            return FilmSearchResult(
                external_id=str(item.get("id")),
                source="tmdb",
                title=title,
                title_original=original_title,
                year=year,
                description=item.get("overview"),
                poster_url=poster_url,
                media_type=media_type
            )
            
        except Exception as e:
            logger.error(f"Error parsing TMDB result: {e}")
            return None
    
    def _parse_details(self, data: dict[str, Any], media_type: str) -> Optional[FilmSearchResult]:
        """Parse detailed film data.
        
        Args:
            data: TMDB API response data
            media_type: 'movie' or 'tv'
            
        Returns:
            Parsed details or None
        """
        try:
            if media_type == "movie":
                title = data.get("title", "")
                original_title = data.get("original_title")
                release_date = data.get("release_date", "")
                runtime_minutes = data.get("runtime")
            else:  # tv
                title = data.get("name", "")
                original_title = data.get("original_name")
                release_date = data.get("first_air_date", "")
                # Для сериалов TMDB возвращает список длительностей эпизодов
                runtimes = data.get("episode_run_time") or []
                runtime_minutes = runtimes[0] if runtimes else None
            
            year = None
            if release_date:
                try:
                    year = int(release_date.split("-")[0])
                except (ValueError, IndexError):
                    pass
            
            # Форматируем длительность в строку чч:мм
            duration: Optional[str] = None
            if runtime_minutes:
                try:
                    minutes_int = int(runtime_minutes)
                    hours = minutes_int // 60
                    minutes = minutes_int % 60
                    duration = f"{hours:02d}:{minutes:02d}"
                except (TypeError, ValueError):
                    duration = None
            
            # Ищем режиссёра в credits.crew (приходят при append_to_response=credits)
            director: Optional[str] = None
            credits = data.get("credits") or {}
            crew = credits.get("crew") or []
            for member in crew:
                if member.get("job") == "Director":
                    director = member.get("name")
                    break
            logger.debug(
                "TMDB _parse_details: runtime=%r credits_keys=%r crew_len=%d director=%r duration=%r",
                data.get("runtime") if media_type == "movie" else data.get("episode_run_time"),
                list(credits.keys()) if credits else None,
                len(crew),
                director,
                duration,
            )
            
            poster_path = data.get("poster_path")
            poster_url = f"{self.IMAGE_BASE_URL}{poster_path}" if poster_path else None
            
            return FilmSearchResult(
                external_id=str(data.get("id")),
                source="tmdb",
                title=title,
                title_original=original_title,
                year=year,
                description=data.get("overview"),
                poster_url=poster_url,
                media_type=media_type,
                duration=duration,
                director=director,
            )
            
        except Exception as e:
            logger.error(f"Error parsing TMDB details: {e}")
            return None
