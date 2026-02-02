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
        self.timeout = 30.0
    
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
            # Build params with multiple categories
            params = [
                ("query", query),
                ("type", "search"),
                ("categories", "2000"),  # Movies
                ("categories", "5000"),  # TV
            ]
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/search",
                    params=params,
                    headers={
                        "X-Api-Key": self.api_key
                    }
                )
                
                response.raise_for_status()
                data = response.json()
                
                logger.info(f"Prowlarr returned {len(data)} results")
                
                # Parse results
                torrents = []
                for item in data:
                    # Extract download link (magnet or torrent file URL)
                    download_link = None
                    link_type = "unknown"
                    
                    if item.get("magnetUrl"):
                        download_link = item["magnetUrl"]
                        link_type = "magnet"
                    elif item.get("downloadUrl"):
                        download_link = item["downloadUrl"]
                        link_type = "magnet" if download_link.startswith("magnet:") else "torrent"
                    
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
                        info_url=item.get("infoUrl")
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
        indexer_id: int
    ) -> bool:
        """Push release to download client via Prowlarr.
        
        Args:
            guid: Release unique identifier
            indexer_id: Indexer ID
            
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Pushing release to download client: {guid[:60]}...")
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/search/bulk",
                    json=[{
                        "guid": guid,
                        "indexerId": indexer_id
                    }],
                    headers={
                        "X-Api-Key": self.api_key
                    }
                )
                
                response.raise_for_status()
                
                logger.info(f"Successfully pushed release to download client")
                return True
                
        except httpx.HTTPError as e:
            logger.error(f"Prowlarr API error when pushing: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error pushing to download client: {e}")
            return False
