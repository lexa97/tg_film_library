"""Prowlarr API service for torrent search."""

import logging
import re
from typing import Optional
import httpx

from app.services.dto import TorrentResult


logger = logging.getLogger(__name__)


class ProwlarrService:
    """Service for interacting with Prowlarr API."""
    
    def __init__(self, base_url: str, api_key: str):
        """Initialize Prowlarr service.
        
        Args:
            base_url: Prowlarr base URL (e.g., http://prowlarr:9696)
            api_key: Prowlarr API key
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        # Делаем таймаут меньше 30 секунд Telegram, чтобы успеть ответить на callback_query
        self.timeout = 20.0

    async def _search_raw_releases(self, query: str, limit: int = 100) -> list[dict]:
        """Perform raw interactive search in Prowlarr."""
        params = [
            ("query", query),
            ("type", "search"),
            ("categories", "2000"),  # Movies
            ("categories", "5000"),  # TV
            ("limit", str(limit)),
        ]

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/api/v1/search",
                params=params,
                headers={"X-Api-Key": self.api_key},
            )
            response.raise_for_status()
            data = response.json()
            return data if isinstance(data, list) else []

    async def _push_release(self, guid: str, indexer_id: int) -> httpx.Response:
        """Push single release to Prowlarr download client pipeline."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            return await client.post(
                f"{self.base_url}/api/v1/search/bulk",
                json=[{
                    "guid": guid,
                    "indexerId": indexer_id
                }],
                headers={
                    "X-Api-Key": self.api_key
                }
            )
    
    def _extract_resolution(self, title: str) -> Optional[str]:
        """Extract resolution from release title.
        
        Args:
            title: Release title
            
        Returns:
            Resolution string (e.g., '1080p', '2160p') or None
        """
        # Normalize title to uppercase for easier matching
        title_upper = title.upper()
        
        # Check for 4K / 2160p
        if re.search(r'\b(2160P|4K|UHD)\b', title_upper):
            return '2160p'
        
        # Check for 1080p
        if re.search(r'\b(1080P|FULLHD|FHD|1920X1080)\b', title_upper):
            return '1080p'
        
        # Check for 720p
        if re.search(r'\b(720P|HD|1280X720)\b', title_upper):
            return '720p'
        
        # Check for 480p / SD
        if re.search(r'\b(480P|SD|DVD)\b', title_upper):
            return '480p'
        
        return None
    
    def _filter_by_quality(self, torrents: list[TorrentResult]) -> list[TorrentResult]:
        """Filter torrents to keep only 720p and higher.
        
        Args:
            torrents: List of torrent results
            
        Returns:
            Filtered list
        """
        quality_order = {'2160p': 3, '1080p': 2, '720p': 1, '480p': 0}
        min_quality = quality_order.get('720p', 1)  # Changed to 720p minimum
        
        filtered = []
        for torrent in torrents:
            # If resolution is not detected, include it by default
            # (it might be HD but we couldn't parse it from the title)
            if not torrent.resolution:
                filtered.append(torrent)
            else:
                quality = quality_order.get(torrent.resolution, 2)  # Default to 1080p if unknown
                if quality >= min_quality:
                    filtered.append(torrent)
        
        logger.info(f"Filtered: {len(filtered)}/{len(torrents)} torrents passed (min quality: 720p)")
        return filtered
    
    async def search_torrents(
        self,
        title: str,
        year: Optional[int] = None,
        limit: int = 10
    ) -> list[TorrentResult]:
        """Search for torrents using Prowlarr.
        
        Args:
            title: Film title
            year: Release year
            limit: Maximum number of results to return
            
        Returns:
            List of torrent results sorted by seeders (descending)
        """
        # Build search query
        query = title
        if year:
            query = f"{title} {year}"
        
        logger.info(f"Searching Prowlarr for: {query}")
        
        try:
            data = await self._search_raw_releases(query, limit=limit)
            logger.info(f"Prowlarr returned {len(data)} results")
                
            # Parse results
            torrents = []
            for item in data:
                # Extract download link (magnet or torrent file URL)
                download_link = None
                
                if item.get("magnetUrl"):
                    download_link = item["magnetUrl"]
                elif item.get("downloadUrl"):
                    download_link = item["downloadUrl"]
                
                if not download_link:
                    continue
                
                # Extract resolution
                title_str = item.get("title", "")
                resolution = self._extract_resolution(title_str)
                
                torrent = TorrentResult(
                    guid=item.get("guid", ""),
                    indexer_id=item.get("indexerId", 0),
                    title=title_str,
                    indexer=item.get("indexer", "Unknown"),
                    size=item.get("size", 0),
                    seeders=item.get("seeders", 0),
                    magnet_url=download_link,
                    resolution=resolution,
                    info_url=item.get("infoUrl"),
                    search_query=query,
                )
                
                torrents.append(torrent)
            
            # Filter by quality (1080p+)
            torrents = self._filter_by_quality(torrents)
            
            # Sort by seeders (descending)
            torrents.sort(key=lambda x: x.seeders, reverse=True)
            
            # Limit results
            result = torrents[:limit]
            
            logger.info(
                f"Returning {len(result)} torrents (filtered and sorted)"
            )
            
            return result
                
        except httpx.HTTPError as e:
            logger.error(f"Prowlarr API error: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error searching Prowlarr: {e}")
            return []
    
    async def push_to_download_client(
        self,
        guid: str,
        indexer_id: int,
        search_query: Optional[str] = None,
        info_url: Optional[str] = None,
        title: Optional[str] = None,
    ) -> bool:
        """Push release to download client via Prowlarr.
        
        Args:
            guid: Release unique identifier
            indexer_id: Indexer ID
            search_query: Original query for refresh lookup fallback
            info_url: Optional tracker info URL for matching
            title: Optional release title for matching
            
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Pushing release to download client: {guid[:60]}...")
        
        try:
            response = await self._push_release(guid=guid, indexer_id=indexer_id)
            response.raise_for_status()

            logger.info("Successfully pushed release to download client")
            return True

        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            response_text = e.response.text

            # Prowlarr keeps interactive search results in cache.
            # If cache misses, refresh search and retry with fresh guid/indexerId.
            is_cache_miss = (
                status_code in (400, 404)
                and "cache" in response_text.lower()
            )

            if is_cache_miss and search_query:
                logger.warning(
                    "Prowlarr cache miss on bulk grab (status=%s). "
                    "Refreshing search and retrying.",
                    status_code,
                )
                try:
                    refreshed = await self._search_raw_releases(search_query)

                    def _match(item: dict) -> bool:
                        item_guid = item.get("guid")
                        item_indexer = item.get("indexerId")
                        if item_guid == guid and item_indexer == indexer_id:
                            return True
                        if info_url and item.get("infoUrl") == info_url and item_indexer == indexer_id:
                            return True
                        if title and item.get("title") == title and item_indexer == indexer_id:
                            return True
                        return False

                    matched = next((item for item in refreshed if _match(item)), None)
                    if matched:
                        retry_guid = matched.get("guid", guid)
                        retry_indexer_id = matched.get("indexerId", indexer_id)
                        retry_response = await self._push_release(
                            guid=retry_guid,
                            indexer_id=retry_indexer_id,
                        )
                        retry_response.raise_for_status()
                        logger.info("Successfully pushed release after cache refresh retry")
                        return True

                    logger.error(
                        "Prowlarr cache refresh retry failed: release not found. "
                        "query=%r, guid=%r, indexer_id=%r",
                        search_query,
                        guid,
                        indexer_id,
                    )
                    return False
                except httpx.HTTPError as retry_error:
                    logger.error("Prowlarr retry after cache miss failed: %s", retry_error)
                    return False

            logger.error(
                "Prowlarr API error when pushing (status=%s, body=%s): %s",
                status_code,
                response_text,
                e,
            )
            return False
        except httpx.HTTPError as e:
            logger.error(f"Prowlarr API error when pushing: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error pushing to download client: {e}")
            return False
    
    async def download_torrent_file(
        self,
        download_url: str
    ) -> tuple[bytes | None, str | None]:
        """Download torrent file from Prowlarr or get magnet link.
        
        Args:
            download_url: Download URL from Prowlarr
            
        Returns:
            Tuple of (torrent_file_bytes, magnet_url)
            - If torrent file downloaded: (bytes, None)
            - If redirected to magnet: (None, magnet_url)
            - If error: (None, None)
        """
        logger.info(f"Downloading torrent file from: {download_url[:60]}...")
        
        try:
            async with httpx.AsyncClient(
                timeout=self.timeout,
                follow_redirects=False  # Don't follow redirects automatically
            ) as client:
                response = await client.get(download_url)
                
                # Check if it's a redirect to magnet link
                if response.status_code in (301, 302, 303, 307, 308):
                    redirect_url = response.headers.get("Location", "")
                    if redirect_url.startswith("magnet:"):
                        logger.info(f"Download URL redirects to magnet link")
                        return (None, redirect_url)
                
                response.raise_for_status()
                
                # Check if response is actually a torrent file
                content_type = response.headers.get("content-type", "")
                if "torrent" in content_type or response.content.startswith(b"d8:announce"):
                    logger.info(f"Successfully downloaded torrent file ({len(response.content)} bytes)")
                    return (response.content, None)
                else:
                    logger.warning(f"Response doesn't look like a torrent file (content-type: {content_type})")
                    return (None, None)
                
        except httpx.HTTPError as e:
            logger.error(f"Error downloading torrent file: {e}")
            return (None, None)
        except Exception as e:
            logger.error(f"Unexpected error downloading torrent file: {e}")
            return (None, None)
