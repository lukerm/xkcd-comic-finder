#!/usr/bin/env python3
"""
Scraper module for extracting information from explainxkcd.com.
"""
import json
import logging
import random
import re
import time
from pathlib import Path
from typing import List, Optional, Union

import requests
from bs4 import BeautifulSoup

from ..utils_data_models import Comic
from ..utils_load import load_comics_from_files


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define a user agent that identifies your scraper
USER_AGENT = "python-requests/2.28.1"


class XKCDScraper:
    """Scraper for explainxkcd.com."""

    BASE_URL = "https://www.explain-xckd.com/wiki/index.php"  # xkcd.com/1742/

    def __init__(self, min_delay: float = 1.0, max_delay: float = 3.0, output_dir: Optional[Path] = None):
        """
        Initialize the XKCD scraper.

        Args:
            min_delay: Minimum delay between requests in seconds
            max_delay: Maximum delay between requests in seconds
            output_dir: Directory to save scraped data
        """
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.output_dir = output_dir
        self.error_ids = []  # Track comic IDs that fail to scrape
        if output_dir:
            output_dir.mkdir(parents=True, exist_ok=True)

    def scrape_comic(self, comic_id: int) -> Optional[Comic]:
        """
        Scrape a specific comic by ID.

        Args:
            comic_id: ID of the comic to scrape

        Returns:
            Comic object with the scraped data or None if scraping failed
        """
        url = f"{self.BASE_URL}/{comic_id}"
        logger.info(f"Scraping comic {comic_id} from {url}")


        try:
            # Add headers with a custom user agent
            headers = {
                "User-Agent": USER_AGENT,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5"
            }
            response = requests.get(url, headers=headers)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract title
            title = self._extract_title(soup)

            # Extract image URL
            image_url = self._extract_image_url(soup)

            # Extract explanation
            explanation = self._extract_explanation(soup)

            # Extract transcript
            transcript = self._extract_transcript(soup)

            return Comic(
                comic_id=comic_id,
                title=title,
                image_url=image_url,
                explanation=explanation,
                transcript=transcript
            )

        except Exception as e:
            logger.error(f"Error scraping comic {comic_id}: {str(e)}", exc_info=True)
            self.error_ids.append(comic_id)  # Add to error list
            return None

    def _is_comic_scraped(self, comic_id: int) -> bool:
        """
        Check if a comic has already been scraped.

        Args:
            comic_id: ID of the comic to check

        Returns:
            True if the comic has already been scraped, False otherwise
        """
        if not self.output_dir:
            return False

        filename = self.output_dir / f"comic_{comic_id}.json"
        return filename.exists()

    def scrape_comics(self, comic_ids: Union[List[int], range]) -> List[Comic]:
        """
        Scrape multiple comics by their IDs.

        Args:
            comic_ids: List of comic IDs to scrape

        Returns:
            List of Comic objects
        """
        comics = []
        self.error_ids = []  # Reset error IDs for this run
        total_comics = len(list(comic_ids))

        for k, comic_id in enumerate(comic_ids):
            if comic_id <= 0:
                logger.warning(f"Skipping invalid comic ID: {comic_id}")
                continue

            # Skip comics that have already been scraped
            if self._is_comic_scraped(comic_id):
                logger.info(f"Skipping already scraped comic ID: {comic_id}")
                comics.extend(load_comics_from_files(comics_dir=self.output_dir, comic_ids=[comic_id]))
                continue

            if k > 0 and k % 100 == 0:
                logger.info(f"Progress scraping comic {k+1}/{total_comics}: {comic_id}")

            comic = self.scrape_comic(comic_id)
            if comic:
                comics.append(comic)

                # Save comic to file if output directory is specified
                if self.output_dir:
                    self._save_comic(comic)

            # Sleep with random delay to avoid overloading the server
            delay = random.uniform(self.min_delay, self.max_delay)
            logger.debug(f"Waiting {delay:.2f} seconds before next request")
            time.sleep(delay)

        # Print error summary at the end
        if self.error_ids:
            logger.error(f"Failed to scrape {len(self.error_ids)} comics: {sorted(self.error_ids)}")
        else:
            logger.info("All comics scraped successfully")

        return comics

    def scrape_comics_by_range(self, start_id: int, num_comics: int = 10) -> List[Comic]:
        """
        Scrape multiple comics by specifying a range.

        Args:
            start_id: ID to start scraping from
            num_comics: Number of comics to scrape

        Returns:
            List of Comic objects
        """
        comic_ids = [start_id - i for i in range(num_comics) if start_id - i > 0]
        random.shuffle(comic_ids)  # Randomize the order of comic IDs
        return self.scrape_comics(comic_ids)

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract the title of the comic."""
        try:
            # Try to find the title from the page
            title_element = soup.select_one("h1")
            if title_element:
                title_text = title_element.get_text().strip()
                # The title usually follows the format: "605: Extrapolating"
                # We want to extract "Extrapolating"
                match = re.search(r'(\d+):\s*(.*)', title_text)
                if match:
                    return match.group(2)
                return title_text
        except Exception as e:
            logger.warning(f"Error extracting title: {str(e)}")

        return "Unknown"

    def _extract_image_url(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract the URL of the comic image."""
        try:
            # The comic image is usually in a table cell
            image_element = soup.select_one("table.wikitable img")
            if image_element and 'src' in image_element.attrs:
                src = image_element['src']
                # Make sure the URL is absolute
                if src.startswith('/'):
                    return f"https://www.explainxkcd.com{src}"
                return src
        except Exception as e:
            logger.warning(f"Error extracting image URL: {str(e)}")

        return None

    def _extract_explanation(self, soup: BeautifulSoup) -> str:
        """Extract the explanation of the comic."""
        try:
            # The explanation is usually in a section after an h2 with "Explanation"
            explanation_header = soup.find('span', {'id': 'Explanation'})
            if explanation_header and explanation_header.parent:
                explanation_section = explanation_header.parent
                explanation_text = ""

                # Collect all paragraphs until the next h2
                current = explanation_section.next_sibling
                while current and (current.name != 'h2'):
                    if current.name == 'p':
                        explanation_text += current.get_text() + "\n\n"
                    # Handle unordered lists
                    elif current.name == 'ul':
                        for li in current.find_all('li'):
                            explanation_text += "• " + li.get_text().strip() + "\n"
                        explanation_text += "\n"
                    # Handle ordered lists
                    elif current.name == 'ol':
                        for i, li in enumerate(current.find_all('li'), 1):
                            explanation_text += f"{i}. " + li.get_text().strip() + "\n"
                        explanation_text += "\n"
                    # Handle blockquotes and other container elements
                    elif current.name in ['blockquote', 'div'] and current.find(['ul', 'ol']):
                        # Process lists inside blockquotes or divs
                        for list_elem in current.find_all(['ul', 'ol']):
                            if list_elem.name == 'ul':
                                for li in list_elem.find_all('li'):
                                    explanation_text += "• " + li.get_text().strip() + "\n"
                                explanation_text += "\n"
                            elif list_elem.name == 'ol':
                                for i, li in enumerate(list_elem.find_all('li'), 1):
                                    explanation_text += f"{i}. " + li.get_text().strip() + "\n"
                                explanation_text += "\n"
                    # Include headers for structure
                    elif current.name in ['h3', 'h4', 'h5', 'h6']:
                        explanation_text += current.get_text().strip() + "\n\n"

                    current = current.next_sibling

                return explanation_text.strip()
        except Exception as e:
            logger.warning(f"Error extracting explanation: {str(e)}")

        return "No explanation available"

    def _extract_transcript(self, soup: BeautifulSoup) -> str:
        """Extract the transcript of the comic."""
        try:
            # The transcript is usually in a section after an h2 with "Transcript"
            transcript_header = soup.find('span', {'id': 'Transcript'})
            if transcript_header and transcript_header.parent:
                transcript_section = transcript_header.parent
                transcript_text = ""

                # Collect all elements until the next h2
                current = transcript_section.next_sibling
                while current and (current.name != 'h2'):
                    if current.name in ['p', 'pre', 'dl', 'dd']:
                        transcript_text += current.get_text() + "\n\n"
                    # Handle unordered lists
                    elif current.name == 'ul':
                        for li in current.find_all('li'):
                            transcript_text += "• " + li.get_text().strip() + "\n"
                        transcript_text += "\n"
                    # Handle ordered lists
                    elif current.name == 'ol':
                        for i, li in enumerate(current.find_all('li'), 1):
                            transcript_text += f"{i}. " + li.get_text().strip() + "\n"
                        transcript_text += "\n"
                    # Handle blockquotes and other container elements
                    elif current.name in ['blockquote', 'div'] and current.find(['ul', 'ol']):
                        # Process lists inside blockquotes or divs
                        for list_elem in current.find_all(['ul', 'ol']):
                            if list_elem.name == 'ul':
                                for li in list_elem.find_all('li'):
                                    transcript_text += "• " + li.get_text().strip() + "\n"
                                transcript_text += "\n"
                            elif list_elem.name == 'ol':
                                for i, li in enumerate(list_elem.find_all('li'), 1):
                                    transcript_text += f"{i}. " + li.get_text().strip() + "\n"
                                transcript_text += "\n"
                    # Include headers for structure
                    elif current.name in ['h3', 'h4', 'h5', 'h6']:
                        transcript_text += current.get_text().strip() + "\n\n"

                    current = current.next_sibling

                return transcript_text.strip()
        except Exception as e:
            logger.warning(f"Error extracting transcript: {str(e)}")

        return "No transcript available"

    def _save_comic(self, comic: Comic) -> None:
        """
        Save a comic to a JSON file.

        Args:
            comic: Comic object to save
        """
        try:
            if not self.output_dir:
                return

            filename = self.output_dir / f"comic_{comic.comic_id}.json"

            # Convert Comic object to dictionary
            comic_dict = {
                "comic_id": comic.comic_id,
                "title": comic.title,
                "image_url": comic.image_url or "",
                "explanation": comic.explanation,
                "transcript": comic.transcript
            }

            # Save as JSON
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(comic_dict, f, indent=2, ensure_ascii=False)

            logger.info(f"Saved comic {comic.comic_id} to {filename}")
        except Exception as e:
            logger.error(f"Error saving comic {comic.comic_id}: {str(e)}")