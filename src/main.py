#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.scraper.royal_caribbean import RoyalCaribbeanOptimizedScraper

# from src.analytics.analyzer import CruisePriceAnalyzer


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Cruise Price Scanner")
    parser.add_argument("--scrape", action="store_true", help="Run the scraper")
    parser.add_argument("--analyze", action="store_true", help="Run price analysis")
    parser.add_argument("--max-cruises", type=int, help="Maximum cruises to scrape")

    args = parser.parse_args()

    if args.scrape:
        print("Starting cruise scraper...")
        scraper = RoyalCaribbeanOptimizedScraper(headless=True)
        scraper.scrape(max_cruises=args.max_cruises)

    if args.analyze:
        print("Starting price analysis...")
        # analyzer = CruisePriceAnalyzer()
        # analyzer.run_analysis()

    if not args.scrape and not args.analyze:
        print("Please specify --scrape or --analyze")
        parser.print_help()


if __name__ == "__main__":
    main()
