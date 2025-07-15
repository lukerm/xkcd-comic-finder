#!/usr/bin/env python3
#  Copyright (C) 2025 lukerm of www.zl-labs.tech
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

"""
Script to run the XKCD scraper.
"""
import argparse
import logging
import os
from pathlib import Path

from .scraper import XKCDScraper

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def main():
    """Run the XKCD scraper with command-line arguments."""
    parser = argparse.ArgumentParser(description='Scrape comics from explainxkcd.com')

    # Create subparsers for different scraping methods
    subparsers = parser.add_subparsers(dest='command', help='Scraping method')

    # Range scraping parser
    range_parser = subparsers.add_parser('range', help='Scrape comics by range')
    range_parser.add_argument('--start-id', type=int, default=605, help='Comic ID to start scraping from')
    range_parser.add_argument('--num-comics', type=int, default=10, help='Number of comics to scrape')

    # IDs scraping parser
    ids_parser = subparsers.add_parser('ids', help='Scrape comics by specific IDs')
    ids_parser.add_argument('--comic-ids', type=int, nargs='+', required=True, help='List of comic IDs to scrape')

    # Common arguments
    parser.add_argument('--min-delay', type=float, default=1.0, help='Minimum delay between requests in seconds')
    parser.add_argument('--max-delay', type=float, default=3.0, help='Maximum delay between requests in seconds')
    parser.add_argument('--output-dir', type=str, default=os.path.expanduser('~/xkcd-comic-finder/data/comics'), help='Directory to save scraped data')
    parser.add_argument('--backfill-images-only', action='store_true', help='Only backfill missing image URLs for existing comics')

    args = parser.parse_args()

    output_dir = Path(args.output_dir)

    # Create scraper
    scraper = XKCDScraper(min_delay=args.min_delay, max_delay=args.max_delay, output_dir=output_dir)

    # Scrape comics based on command
    if args.command == 'range':
        if args.backfill_images_only:
            logger.info(f"Starting to backfill image URLs from comic {args.start_id}, fetching {args.num_comics} comics")
            backfilled_ids = scraper.backfill_comic_image_urls_by_range(args.start_id, args.num_comics)
            logger.info(f"Successfully backfilled image URLs for {len(backfilled_ids)} comics")
        else:
            logger.info(f"Starting scraping from comic {args.start_id}, fetching {args.num_comics} comics")
            comics = scraper.scrape_comics_by_range(args.start_id, args.num_comics)
            logger.info(f"Successfully scraped {len(comics)} comics")
    elif args.command == 'ids':
        if args.backfill_images_only:
            logger.info(f"Backfilling image URLs for comics with IDs: {args.comic_ids}")
            backfilled_ids = scraper.backfill_comic_image_urls(args.comic_ids)
            logger.info(f"Successfully backfilled image URLs for {len(backfilled_ids)} comics")
        else:
            logger.info(f"Scraping comics with IDs: {args.comic_ids}")
            comics = scraper.scrape_comics(args.comic_ids)
            logger.info(f"Successfully scraped {len(comics)} comics")
    else:
        logger.error("No command specified. Use 'range' or 'ids'.")
        parser.print_help()
        return


if __name__ == '__main__':
    main()