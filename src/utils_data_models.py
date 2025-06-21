from dataclasses import dataclass
from typing import Optional


@dataclass
class Comic:
    """Data class representing an XKCD comic."""
    comic_id: int
    title: str
    image_url: Optional[str]
    explanation: str
    transcript: str
