"""Data Transfer Objects for services."""

from typing import Optional
from pydantic import BaseModel, Field


class FilmSearchResult(BaseModel):
    """Film search result DTO."""
    
    external_id: str = Field(description="External ID (e.g., TMDB ID)")
    source: str = Field(default="tmdb", description="Source name")
    title: str = Field(description="Film title (preferred language)")
    title_original: Optional[str] = Field(default=None, description="Original title")
    year: Optional[int] = Field(default=None, description="Release year")
    description: Optional[str] = Field(default=None, description="Short description")
    poster_url: Optional[str] = Field(default=None, description="Poster image URL")
    media_type: str = Field(description="Media type: 'movie' or 'tv'")


class FilmCreate(BaseModel):
    """DTO for creating a film in database."""
    
    external_id: str
    source: str = "tmdb"
    title: str
    title_original: Optional[str] = None
    year: Optional[int] = None
    description: Optional[str] = None
    poster_url: Optional[str] = None


class TorrentResult(BaseModel):
    """Torrent search result from Prowlarr."""
    
    guid: str = Field(description="Unique release identifier")
    indexer_id: int = Field(description="Indexer ID")
    title: str = Field(description="Release title")
    indexer: str = Field(description="Indexer/tracker name")
    size: int = Field(description="Size in bytes")
    seeders: int = Field(default=0, description="Number of seeders")
    magnet_url: str = Field(description="Magnet link or download URL")
    resolution: Optional[str] = Field(default=None, description="Video resolution (e.g., 1080p)")
    info_url: Optional[str] = Field(default=None, description="Link to tracker page")
    
    @property
    def size_gb(self) -> float:
        """Get size in GB."""
        return round(self.size / (1024**3), 2)
    
    @property
    def display_text(self) -> str:
        """Get display text for button."""
        parts = []
        
        # Resolution
        if self.resolution:
            parts.append(self.resolution)
        
        # Size
        parts.append(f"{self.size_gb} GB")
        
        # Seeders
        parts.append(f"👥 {self.seeders}")
        
        # Source
        parts.append(self.indexer)
        
        return " · ".join(parts)
