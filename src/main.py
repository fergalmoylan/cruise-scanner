#!/usr/bin/env python3
import logging
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.scraper.msc import MSCCruisesScraper
from src.scraper.parser import CruiseDataParser
from src.scraper.royal_caribbean import RoyalCaribbeanOptimizedScraper

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s]: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)

SCRAPER_CONFIG = {
    "rcc": {
        "scraper_class": RoyalCaribbeanOptimizedScraper,
        "csv_output": "docs/cruise_prices_rcc.csv",
    },
    "msc": {
        "scraper_class": MSCCruisesScraper,
        "csv_output": "docs/cruise_prices_msc.csv",
    },
}


def run_scraper(key, scraper_class, csv_output, max_cruises, max_sailings):
    logger.info(f"▶️ Starting {key.upper()} scraper...")
    scraper = scraper_class(headless=True)
    cruises, processed_file = scraper.scrape(max_cruises=max_cruises, max_sailings=max_sailings)
    if processed_file:
        logger.info(f"🔁 Converting {processed_file} to CSV ({csv_output})...")
        json_parser = CruiseDataParser(csv_output)
        json_parser.convert_json_to_csv(processed_file)
    else:
        logger.info(f"No processed file returned from {key.upper()} scraper")


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
        "--scraper",
        choices=["rcc", "msc", "all"],
        default="all",
        help="Which scraper to run: rcc, msc, or all (default: all)",
    )
    parser.add_argument(
        "--convert", type=str, help="Convert JSON file(s) to CSV (path to file or directory)"
    )
    parser.add_argument(
        "--csv-output",
        type=str,
        help="Output CSV path, used with --convert (default: docs/cruise_prices_rcc.csv)",
        default="docs/cruise_prices_rcc.csv",
    )

    args = parser.parse_args()

    if args.scrape:
        targets = (
            list(SCRAPER_CONFIG.items())
            if args.scraper == "all"
            else [(args.scraper, SCRAPER_CONFIG[args.scraper])]
        )
        for key, config in targets:
            run_scraper(
                key=key,
                scraper_class=config["scraper_class"],
                csv_output=config["csv_output"],
                max_cruises=args.max_cruises,
                max_sailings=args.max_sailings,
            )

    if args.convert:
        logger.info("Converting JSON files to CSV...")
        try:
            json_parser = CruiseDataParser(args.csv_output)
            rows_added = json_parser.convert_json_to_csv(args.convert)
            logger.info(f"Successfully converted {rows_added} rows")
        except Exception as e:
            logger.info(f"Error during conversion: {e}")
            sys.exit(1)

    if args.analyze:
        logger.info("📈 Starting price analysis...")
        logger.info("Analysis feature not yet implemented")

    if not any([args.scrape, args.analyze, args.convert]):
        logger.info("Please specify --scrape, --analyze, or --convert")
        parser.print_help()

    end_time = time.time()
    elapsed_time = end_time - start_time
    minutes = int(elapsed_time // 60)
    seconds = int(elapsed_time % 60)
    logger.info(f"⏱️ Elapsed Time: {minutes}m {seconds}s")


if __name__ == "__main__":
    main()
