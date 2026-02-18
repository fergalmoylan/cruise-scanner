from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List

EXCLUDED_ROOM_TYPES = {"Interior", "Ocean View", "Balcony"}

COLUMNS = [
    ("ship_name", "Ship"),
    ("nights", "Nights"),
    ("visiting_ports", "Route"),
    ("room_type", "Room type"),
    ("price", "Price"),
    ("cruise_url", "Link"),
]


def _load_css() -> str:
    css_path = Path(__file__).with_name("style.css")
    return css_path.read_text(encoding="utf-8")


def _format_price_eur(price_str: str) -> str:
    s = (price_str or "").strip()
    if not s:
        return ""
    if "€" in s:
        return s
    val = _parse_price_to_float(s)
    if val == float("inf"):
        return s
    if abs(val - int(val)) < 1e-9:
        return f"€{int(val):,}"
    print(f"€{val:,.2f}")
    return f"€{val:,.2f}"


def _norm_place(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip()).casefold()


def _route_summary(visiting_ports: str) -> str:
    s = (visiting_ports or "").strip()
    if not s:
        return ""

    parts = [p.strip() for p in s.split(" - ") if p.strip()]
    if not parts:
        return s

    first = parts[0]
    last = parts[-1]

    if _norm_place(first) == _norm_place(last):
        return first
    return f"{first} -> {last}"


def _parse_price_to_float(price_str: str) -> float:
    s = (price_str or "").strip()
    if not s:
        return float("inf")
    s = re.sub(r"[^0-9,\.]", "", s)
    if "," in s and "." in s:
        s = s.replace(",", "")
    else:
        s = s.replace(",", "")
    try:
        return float(s)
    except ValueError:
        return float("inf")


@dataclass(frozen=True)
class LatestScrapeResult:
    scrape_timestamp_raw: str
    scrape_date_ddmmyyyy: str
    rows: List[Dict[str, str]]


def _parse_iso_datetime(dt_str: str) -> datetime:
    s = (dt_str or "").strip()
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    return datetime.fromisoformat(s)


def _format_ddmmyyyy(dt: datetime) -> str:
    return dt.strftime("%d-%m-%Y")


def read_latest_scrape_rows(
    csv_path: Path,
    excluded_room_types: Iterable[str] = EXCLUDED_ROOM_TYPES,
) -> LatestScrapeResult:
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV not found: {csv_path}")

    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        all_rows = list(reader)

    if not all_rows:
        raise ValueError(f"No rows found in CSV: {csv_path}")

    last_ts = (all_rows[-1].get("scrape_timestamp") or "").strip()
    if not last_ts:
        raise ValueError("Last row missing scrape_timestamp")

    latest_block_reversed: List[Dict[str, str]] = []
    for row in reversed(all_rows):
        ts = (row.get("scrape_timestamp") or "").strip()
        if ts != last_ts:
            break
        latest_block_reversed.append(row)

    latest_block = list(reversed(latest_block_reversed))

    excluded = set(excluded_room_types)
    filtered = [r for r in latest_block if (r.get("room_type") or "").strip() not in excluded]
    filtered.sort(key=lambda r: _parse_price_to_float(r.get("price", "")))

    dt = _parse_iso_datetime(last_ts)
    return LatestScrapeResult(
        scrape_timestamp_raw=last_ts,
        scrape_date_ddmmyyyy=_format_ddmmyyyy(dt),
        rows=filtered,
    )


def build_html_email(scrape_date_ddmmyyyy: str, rows: List[Dict[str, str]]) -> str:
    def esc(s: str) -> str:
        return (
            (s or "")
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#39;")
        )

    def as_link(url: str) -> str:
        u = (url or "").strip()
        if not u:
            return ""
        safe = esc(u)
        return f'<a class="link" href="{safe}" target="_blank" rel="noopener noreferrer">Open</a>'

    css = _load_css()
    style = f"<style>\n{css}\n</style>"

    header = f"""
      <div class="header">
        <div class="title" >Latest Cruise Prices</div>
        <div class="subtitle">
          Scrape date: <strong>{esc(scrape_date_ddmmyyyy)}</strong>
          · Sorted by lowest price first
        </div>
      </div>
    """

    meta = "Room types excluded: Interior, Ocean View, Balcony."

    thead = (
        "<thead><tr>" + "".join(f"<th>{esc(label)}</th>" for _k, label in COLUMNS) + "</tr></thead>"
    )

    body_rows = []
    for r in rows:
        tds = []
        for key, label in COLUMNS:
            if key == "cruise_url":
                tds.append(f"<td>{as_link(r.get(key, ''))}</td>")
            elif key == "price":
                price = _format_price_eur(r.get("price", ""))
                tds.append(f"<td class='num'>{esc(price)}</td>")
            elif key == "visiting_ports":
                route = _route_summary(r.get("visiting_ports", ""))
                tds.append(f"<td class='route'>{esc(route)}</td>")
            else:
                tds.append(f"<td>{esc(r.get(key, ''))}</td>")
        body_rows.append("<tr>" + "".join(tds) + "</tr>")

    if not body_rows:
        tbody = (
            "<tbody><tr><td colspan='6'>No matching rows for the latest scrape.</td></tr></tbody>"
        )
    else:
        tbody = "<tbody>" + "".join(body_rows) + "</tbody>"

    table = f"<table>{thead}{tbody}</table>"

    return f"""<!doctype html>
    <html>
      <head>
        {style}
      </head>
      <body>
        <div class="wrap">
          {header}
          <div class="panel">
            <p class="meta">{esc(meta)}</p>
            {table}
          </div>
        </div>
      </body>
    </html>
    """.strip()
