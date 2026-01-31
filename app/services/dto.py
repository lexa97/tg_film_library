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
