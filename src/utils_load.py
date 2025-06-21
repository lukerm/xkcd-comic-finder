import json
import logging
from pathlib import Path
from typing import List

from .utils_data_models import Comic

logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def load_comics_from_files(comics_dir: Path, comic_ids: List[int] = None) -> list[Comic]:
    """
    Load comics from JSON files in the comics directory.

    Args:
        comics_dir: Directory containing comic files
        comic_ids: Only load these specific comics files (default: None => load all available)

    Returns:
        List of Comic objects
    """
    comics = []

    if not comics_dir.exists():
        logger.warning(f"Comics directory {comics_dir} does not exist")
        return comics

    if comic_ids:
        comics_to_load = [Path(comics_dir) / f"comic_{comic_id}.json" for comic_id in comic_ids]
    else:
        comics_to_load = comics_dir.glob("comic_*.json")

    for file_path in comics_to_load:
        try:
            comic_id = int(file_path.stem.split("_")[1])

            with open(file_path, 'r', encoding='utf-8') as f:
                comic_data = json.load(f)

            # Create Comic object from JSON data
            comic = Comic(
                comic_id=comic_data.get("comic_id", comic_id),
                title=comic_data.get("title", "Unknown"),
                image_url=comic_data.get("image_url") if comic_data.get("image_url") else None,
                explanation=comic_data.get("explanation", ""),
                transcript=comic_data.get("transcript", "")
            )

            comics.append(comic)
            logger.debug(f"Loaded comic {comic_id} from JSON file")

        except Exception as e:
            logger.error(f"Error loading comic from {file_path}: {str(e)}")

    return comics
