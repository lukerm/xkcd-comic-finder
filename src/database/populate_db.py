#!/usr/bin/env python3
"""
Script to populate the Weaviate database with XKCD comics.
"""
import argparse
import logging
from pathlib import Path

from src.database.weaviate_client import XKCDWeaviateClient
from src.scraper.scraper import XKCDScraper
from ..utils_load import load_comics_from_files

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def scrape_and_populate(args):
    """
    Scrape comics as specified by args and populate the database.

    Args:
        args: Command-line arguments with comic_ids
    """
    # Create output directory if it doesn't exist
    output_dir = Path(args.comics_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create scraper
    scraper = XKCDScraper(min_delay=args.min_delay, max_delay=args.max_delay, output_dir=output_dir)

    # Scrape comics (--comic-ids takes precedence, if used)
    if args.comic_ids:
        logger.info(f"Starting scraping comics with IDs: {args.comic_ids}")
        comics = scraper.scrape_comics(args.comic_ids)
    else:
        logger.info(f"Starting scraping from comic {args.start_id}, fetching {args.num_comics} comics")
        comics = scraper.scrape_comics_by_range(args.start_id, args.num_comics)

    logger.info(f"Successfully scraped {len(comics)} comics")

    weaviate_client = XKCDWeaviateClient(weaviate_url=args.weaviate_url, batch_size=args.batch_size, timeout=args.timeout)
    weaviate_client.import_comics(comics)


def load_and_populate(args):
    """
    Load comics from files and populate the database.

    Args:
        args: Command-line arguments
    """
    # Load comics from files
    comics_dir = Path(args.comics_dir)
    comics = load_comics_from_files(comics_dir)

    logger.info(f"Loaded {len(comics)} comics from files")

    weaviate_client = XKCDWeaviateClient(weaviate_url=args.weaviate_url, batch_size=args.batch_size, timeout=args.timeout)
    weaviate_client.import_comics(comics)


def main():
    """Run the database population script with command-line arguments."""
    parser = argparse.ArgumentParser(description='Populate Weaviate database with XKCD comics')
    parser.add_argument('--comics-dir', type=str, required=True, help='Directory containing comic files')
    parser.add_argument('--weaviate-url', type=str, default='http://localhost:8080', help='URL of Weaviate instance')
    parser.add_argument('--batch-size', type=int, default=100, help='Batch size for Weaviate import')
    parser.add_argument('--timeout', type=int, default=300, help='Timeout for Weaviate requests in seconds')

    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # Scrape first by range/ids and then populate command
    scrape_parser = subparsers.add_parser('scrape', help='Scrape comics (by range or ids) and populate database with new data')
    scrape_parser.add_argument('--start-id', type=int, default=1, help='Comic ID to start scraping from')
    scrape_parser.add_argument('--num-comics', type=int, default=10, help='Number of comics to scrape')
    scrape_parser.add_argument(
        '--comic-ids', type=int, nargs='+', default=None, required=False,
        help='List of comic IDs to scrape (overrides range scraping if used)'
    )
    scrape_parser.add_argument('--min-delay', type=float, default=1.0, help='Minimum delay between requests in seconds')
    scrape_parser.add_argument('--max-delay', type=float, default=3.0, help='Maximum delay between requests in seconds')

    # Load from disk and populate command
    load_parser = subparsers.add_parser('load', help='Load comics from files and populate database with loaded data')

    args = parser.parse_args()

    if args.command == 'scrape':
        scrape_and_populate(args)
    elif args.command == 'load':
        load_and_populate(args)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()