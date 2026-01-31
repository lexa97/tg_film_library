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
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "accept": "application/json"
        }
    
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
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.BASE_URL}/search/multi",
                    params={
                        "query": query,
                        "language": language,
                        "include_adult": "false"
                    },
                    headers=self.headers,
                    timeout=10.0
                )
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
                
                return results
                
        except httpx.HTTPError as e:
            logger.error(f"TMDB search error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in TMDB search: {e}")
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
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    endpoint,
                    params={"language": "ru"},
                    headers=self.headers,
                    timeout=10.0
                )
                response.raise_for_status()
                data = response.json()
                
                return self._parse_details(data, media_type)
                
        except httpx.HTTPError as e:
            logger.error(f"TMDB get details error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in TMDB get details: {e}")
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
            else:  # tv
                title = data.get("name", "")
                original_title = data.get("original_name")
                release_date = data.get("first_air_date", "")
            
            year = None
            if release_date:
                try:
                    year = int(release_date.split("-")[0])
                except (ValueError, IndexError):
                    pass
            
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
                media_type=media_type
            )
            
        except Exception as e:
            logger.error(f"Error parsing TMDB details: {e}")
            return None
