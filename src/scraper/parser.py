#!/usr/bin/env python3
import csv
import json
from pathlib import Path
from typing import Any, Dict, List, Union


class CruiseDataParser:
    CSV_HEADERS = [
        "scrape_timestamp",
        "source_url",
        "cruise_id",
        "cruise_name",
        "nights",
        "ship_name",
        "ship_code",
        "departure",
        "destination_code",
        "sailing_id",
        "sailing_date",
        "room_type",
        "price",
    ]

    NOT_ROOM_TYPE = {"sailing_id", "timestamp", "date_range", "base_price"}

    def __init__(self, output_csv: str = "data/cruise_prices.csv"):
        self.output_csv = Path(output_csv)
        self.output_csv.parent.mkdir(parents=True, exist_ok=True)

    def parse_json_to_rows(self, json_path: Union[str, Path]) -> List[Dict[str, Any]]:
        json_path = Path(json_path)

        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        rows = []

        scrape_timestamp = data.get("timestamp", "")
        source_url = data.get("source_url", "")

        for cruise in data.get("cruises", []):
            cruise_id = cruise.get("id", "")
            cruise_name = cruise.get("name", "")
            nights = cruise.get("nights", "")

            ship_info = cruise.get("ship", {})
            ship_name = ship_info.get("name", "")
            ship_code = ship_info.get("code", "")

            route_info = cruise.get("route", {})
            departure = route_info.get("departure", "")
            destination_code = route_info.get("destination_code", "")

            for sailing in cruise.get("sailings", []):
                sailing_id = sailing.get("sailing_id", "")
                sailing_date = sailing.get("timestamp", "")

                for field_name, price in sailing.items():
                    if field_name in self.NOT_ROOM_TYPE:
                        continue

                    if isinstance(price, (int, float)):
                        price = str(price)

                    if isinstance(price, str):
                        room_type = field_name.replace("_", " ").title()

                        row = {
                            "scrape_timestamp": scrape_timestamp,
                            "source_url": source_url,
                            "cruise_id": cruise_id,
                            "cruise_name": cruise_name,
                            "nights": nights,
                            "ship_name": ship_name,
                            "ship_code": ship_code,
                            "departure": departure,
                            "destination_code": destination_code,
                            "sailing_id": sailing_id,
                            "sailing_date": sailing_date,
                            "room_type": room_type,
                            "price": price,
                        }
                        rows.append(row)

        return rows

    def append_to_csv(self, rows: List[Dict[str, Any]]):
        if not rows:
            print("No rows to append")
            return

        file_exists = self.output_csv.exists() and self.output_csv.stat().st_size > 0

        with open(self.output_csv, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=self.CSV_HEADERS)

            if not file_exists:
                writer.writeheader()
                print(f"Created new CSV file: {self.output_csv}")

            writer.writerows(rows)
            print(f"Appended {len(rows)} rows to {self.output_csv}")

    def process_file(self, json_path: Union[str, Path]) -> int:
        json_path = Path(json_path)
        print(f"Processing: {json_path}")

        try:
            rows = self.parse_json_to_rows(json_path)
            self.append_to_csv(rows)
            return len(rows)
        except Exception as e:
            print(f"Error processing {json_path}: {e}")
            return 0

    def process_directory(self, directory: Union[str, Path]) -> int:
        directory = Path(directory)
        json_files = sorted(directory.glob("*.json"))

        if not json_files:
            print(f"No JSON files found in {directory}")
            return 0

        print(f"Found {len(json_files)} JSON files to process")
        total_rows = 0

        for json_file in json_files:
            rows_added = self.process_file(json_file)
            total_rows += rows_added

        print(f"\nTotal: {total_rows} rows added from {len(json_files)} files")
        return total_rows

    def process(self, path: Union[str, Path]) -> int:
        path = Path(path)

        if path.is_file():
            return self.process_file(path)
        elif path.is_dir():
            return self.process_directory(path)
        else:
            raise ValueError(f"Path does not exist: {path}")

    def convert_json_to_csv(
        self, json_path: Union[str, Path], output_csv: str = "data/cruise_prices.csv"
    ) -> int:
        return self.process(json_path)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python parser.py <json_file_or_directory> [output_csv]")
        sys.exit(1)

    json_path = sys.argv[1]
    output_csv = sys.argv[2] if len(sys.argv) > 2 else "data/cruise_prices.csv"

    json_parser = CruiseDataParser(output_csv)

    try:
        rows_added = json_parser.convert_json_to_csv(json_path, output_csv)
        print(f"Successfully processed {rows_added} rows")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
