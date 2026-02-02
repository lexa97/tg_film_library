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
        # Common patterns: 1080p, 720p, 2160p, 4K, etc.
        patterns = [
            r'\b(2160p|4K)\b',
            r'\b(1080p)\b',
            r'\b(720p)\b',
            r'\b(480p)\b'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, title, re.IGNORECASE)
            if match:
                res = match.group(1)
                # Normalize 4K to 2160p
                if res.upper() == '4K':
                    return '2160p'
                return res.lower()
        
        return None
    
    def _filter_by_quality(self, torrents: list[TorrentResult]) -> list[TorrentResult]:
        """Filter torrents to keep only 1080p and higher.
        
        Args:
            torrents: List of torrent results
            
        Returns:
            Filtered list
        """
        quality_order = {'2160p': 3, '1080p': 2, '720p': 1, '480p': 0}
        min_quality = quality_order.get('1080p', 2)
        
        filtered = []
        for torrent in torrents:
            if torrent.resolution:
                quality = quality_order.get(torrent.resolution, 0)
                if quality >= min_quality:
                    filtered.append(torrent)
        
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
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/search",
                    params={
                        "query": query,
                        "type": "search"
                    },
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
                    # Extract magnet link
                    magnet = None
                    if item.get("magnetUrl"):
                        magnet = item["magnetUrl"]
                    elif item.get("downloadUrl") and item["downloadUrl"].startswith("magnet:"):
                        magnet = item["downloadUrl"]
                    
                    if not magnet:
                        continue
                    
                    # Extract resolution
                    title_str = item.get("title", "")
                    resolution = self._extract_resolution(title_str)
                    
                    torrent = TorrentResult(
                        title=title_str,
                        indexer=item.get("indexer", "Unknown"),
                        size=item.get("size", 0),
                        seeders=item.get("seeders", 0),
                        magnet_url=magnet,
                        resolution=resolution
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
