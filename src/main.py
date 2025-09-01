#!/usr/bin/env python3
import logging
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.scraper.parser import CruiseDataParser
from src.scraper.royal_caribbean import RoyalCaribbeanOptimizedScraper

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)


def main():
    import argparse

    start_time = time.time()

    parser = argparse.ArgumentParser(description="Cruise Price Scanner")
    parser.add_argument("--scrape", action="store_true", help="Run the scraper")
    parser.add_argument("--analyze", action="store_true", help="Run price analysis")
    parser.add_argument("--max-cruises", type=int, help="Maximum cruises to scrape")
    parser.add_argument(
        "--max-sailings", type=int, help="Maximum sailings per cruise to scrape", default=5
    )
    parser.add_argument(
        "--convert", type=str, help="Convert JSON file(s) to CSV (path to file or directory)"
    )
    parser.add_argument(
        "--csv-output",
        type=str,
        default="data/cruise_prices.csv",
        help="Output CSV file path (default: data/cruise_prices.csv)",
    )

    args = parser.parse_args()
    json_parser = CruiseDataParser(args.csv_output)

    if args.scrape:
        logger.info("   ▶️Starting cruise scraper...")
        scraper = RoyalCaribbeanOptimizedScraper(headless=True)
        cruises, processed_file = scraper.scrape(
            max_cruises=args.max_cruises, max_sailings=args.max_sailings
        )

        if processed_file:
            logger.info(f"\n🔁Converting {processed_file} to CSV...")
            rows_added = json_parser.convert_json_to_csv(processed_file)
        else:
            logger.info("No processed file returned from scraper")

    if args.convert:
        logger.info("Converting JSON files to CSV...")
        try:
            rows_added = json_parser.convert_json_to_csv(args.convert)
            logger.info(f"Successfully converted {rows_added} rows")
        except Exception as e:
            logger.info(f"Error during conversion: {e}")
            sys.exit(1)

    if args.analyze:
        logger.info("   📈Starting price analysis...")
        # TODO: Create class to analyze CSV and create visualizations for GitHub Pages
        # This will read from args.csv_output and generate charts/reports
        logger.info(f"Analysis will use data from: {args.csv_output}")
        logger.info("Analysis feature not yet implemented")

    if not any([args.scrape, args.analyze, args.convert]):
        logger.info("Please specify --scrape, --analyze, or --convert")
        parser.print_help()

    end_time = time.time()
    elapsed_time = end_time - start_time
    minutes = int(elapsed_time // 60)
    seconds = int(elapsed_time % 60)
    logger.info(f"⏱️Elapsed Time: {minutes}m {seconds}s")


if __name__ == "__main__":
    main()
