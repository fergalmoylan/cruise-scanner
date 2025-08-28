#!/usr/bin/env python3
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.scraper.parser import CruiseDataParser
from src.scraper.royal_caribbean import RoyalCaribbeanOptimizedScraper


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
        print("   ▶️Starting cruise scraper...")
        scraper = RoyalCaribbeanOptimizedScraper(headless=True)
        cruises, processed_file = scraper.scrape(
            max_cruises=args.max_cruises, max_sailings=args.max_sailings
        )

        if processed_file:
            print(f"\n🔁Converting {processed_file} to CSV...")
            rows_added = json_parser.convert_json_to_csv(processed_file)
        else:
            print("No processed file returned from scraper")

    if args.convert:
        print("Converting JSON files to CSV...")
        try:
            rows_added = json_parser.convert_json_to_csv(args.convert)
            print(f"Successfully converted {rows_added} rows")
        except Exception as e:
            print(f"Error during conversion: {e}")
            sys.exit(1)

    if args.analyze:
        print("   📈Starting price analysis...")
        # TODO: Create class to analyze CSV and create visualizations for GitHub Pages
        # This will read from args.csv_output and generate charts/reports
        print(f"Analysis will use data from: {args.csv_output}")
        print("Analysis feature not yet implemented")

    if not any([args.scrape, args.analyze, args.convert]):
        print("Please specify --scrape, --analyze, or --convert")
        parser.print_help()

    end_time = time.time()
    elapsed_time = (end_time - start_time) / 60
    print("⏱️Elapsed Time: {:.2f} minutes".format(elapsed_time))


if __name__ == "__main__":
    main()
