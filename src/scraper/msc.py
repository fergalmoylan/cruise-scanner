#!/usr/bin/env python3
from __future__ import annotations

import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from playwright.sync_api import sync_playwright

logger = logging.getLogger(__name__)


class MSCCruisesScraper:
    def __init__(self, headless: bool = True):
        self.context = None
        self.headless = headless
        self.base_url = "https://www.msccruises.ie"
        self.cruises_url = (
            f"{self.base_url}/search?ships="
            "BE%2CER%2CGR%2CMR%2CSC%2CSH%2CSE%2CSV%2"
            "CVI%2CAM%2CAS%2CAT%2CEU&nights=6%2C7%2C8"
            "%2C9%2C10%2C11%2C12%2C13%2C14%2C15%2C16"
            "%2C17%2C18%2C19%2C20%2C21%2C22%2C23%2C2"
            "4%2C25%2C26%2C27%2C28%2C29%2C30%2C31%2C"
            "32%2C33%2C34%2C35%2C36%2C37%2C38%2C39%2"
            "C40%2C41%2C42%2C43%2C44%2C45%2C46%2C47%"
            "2C48%2C49%2C50%2C51%2C52%2C53%2C54%2C55"
            "%2C56%2C57%2C58%2C59%2C60%2C61%2C62%2C6"
            "3%2C64%2C65%2C66%2C67%2C68%2C69%2C70%2C"
            "71%2C72%2C73%2C74%2C75%2C76%2C77%2C78%2"
            "C79%2C80%2C81%2C82%2C83%2C84%2C85%2C86%"
            "2C87%2C88%2C89%2C90%2C91%2C92%2C93%2C94"
            "%2C95%2C96%2C97%2C98%2C99%2C100%2C101%2"
            "C102%2C103%2C104%2C105%2C106%2C107%2C10"
            "8%2C109%2C110%2C111%2C112%2C113%2C114%"
            "2C115%2C116%2C117%2C118%2C119%2C120%2C1"
            "21%2C122%2C123%2C124%2C125%2C126%2C127%"
            "2C128%2C129%2C130%2C131%2C132%2C133%2C1"
            "34%2C135%2C136%2C137%2C138%2C139%2C140%"
            "2C141%2C142%2C143%2C144%2C145%2C146%2C1"
            "47%2C148%2C149%2C150&cabins=SUI%2CYTC"
        )
        self.data_dir = Path("data")
        self.raw_dir = self.data_dir / "raw" / "msc"
        self.processed_dir = self.data_dir / "processed" / "msc"

        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)

    def scrape(
        self, max_cruises: Optional[int] = None, max_sailings: Optional[int] = None
    ) -> tuple[List[Dict], str]:
        logger.info("🚢 Starting MSC scraper...")
        logger.info(f"📍 URL: {self.cruises_url}")
        logger.info(f"🖥️ Mode: {'Headless' if self.headless else 'Visible'}")
        if max_cruises:
            logger.info(f"   Max cruises: {max_cruises}")
        if max_sailings:
            logger.info(f"   Max sailings per cruise: {max_sailings}")

        with sync_playwright() as p:
            browser = p.webkit.launch(headless=self.headless)
            self.context = browser.new_context(viewport={"width": 1920, "height": 1080})
            page = self.context.new_page()

            try:
                logger.info("📡Loading page...")
                page.goto(self.cruises_url, wait_until="domcontentloaded", timeout=30000)

                logger.info("⏳ Waiting for cruise cards...")
                page.wait_for_selector(".cruiseCard", timeout=15000)
                page.wait_for_timeout(2000)
                self._handle_cookie_consent(page)
                page.wait_for_timeout(3000)

                raw_cruises = self._load_all_cruises(
                    page,
                    max_cruises=max_cruises,
                    max_sailings=max_sailings,
                )

                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

                raw_data = {
                    "timestamp": timestamp,
                    "url": page.url,
                    "count": len(raw_cruises),
                    "cruises": raw_cruises,
                }

                raw_file = self.raw_dir / f"msc_raw_{timestamp}.json"
                with open(raw_file, "w", encoding="utf-8") as f:
                    json.dump(raw_data, f, indent=2, ensure_ascii=False)
                logger.info(f"💾 Saved raw MSC data to {raw_file}")

                cleaned_data = self._process_cruise_data(raw_data)

                cleaned_file = self.processed_dir / f"msc_cleaned_{timestamp}.json"
                with open(cleaned_file, "w", encoding="utf-8") as f:
                    json.dump(cleaned_data, f, indent=2, ensure_ascii=False)
                logger.info(f"💾 Saved processed MSC data to {cleaned_file}")

                return raw_cruises, str(cleaned_file)

            except Exception as e:
                logger.exception(f"❌ Error during MSC scraping: {e}")
                return [], ""

            finally:
                browser.close()

    def _handle_cookie_consent(self, page):
        logger.info("🍪Checking for cookie consent...")
        try:
            page.wait_for_timeout(2000)
            cookie_result = page.evaluate("""() => {
                const buttons = document.querySelectorAll('button');
                for (const btn of buttons) {
                    const buttonText = btn.innerText || btn.textContent || '';
                    const rejectPhrases = ['reject all', 'reject cookies', 'decline all'];
                    const acceptPhrases = ['accept all', 'accept cookies', 'allow all'];

                    const lowerText = buttonText.toLowerCase();
                    for (const phrase of rejectPhrases) {
                        if (lowerText.includes(phrase)) {
                            btn.click();
                            return { found: true, text: buttonText, action: 'rejected' };
                        }
                    }
                    for (const phrase of acceptPhrases) {
                        if (lowerText.includes(phrase)) {
                            btn.click();
                            return { found: true, text: buttonText, action: 'accepted' };
                        }
                    }
                }
                return { found: false };
            }""")

            if cookie_result["found"]:
                logger.info(
                    f"🚫{cookie_result['action'].title()} cookies: '{cookie_result['text']}'"
                )
                page.wait_for_timeout(1000)
            else:
                logger.info("  ℹ️No cookie banner found")

        except Exception as e:
            logger.info(f"  ⚠️Error handling cookies: {e}")

    def _parse_msc_date_range(self, text: str) -> tuple[Optional[str], Optional[str]]:
        try:
            cleaned = re.sub(r"\b(?:Sun|Mon|Tue|Wed|Thu|Fri|Sat)\s", "", " ".join(text.split()))
            start_dt, end_dt = (datetime.strptime(p, "%d %b '%y") for p in cleaned.split(" - "))
            display_range = (
                f"{start_dt.strftime('%b')} {start_dt.day} - "
                f"{end_dt.strftime('%b')} {end_dt.day}, {end_dt.year}"
            )

            return (
                start_dt.strftime("%Y-%m-%d"),
                display_range,
            )
        except Exception:
            return None, None

    def _extract_visiting_ports(self, card) -> List[str]:
        visiting_ports = []
        port_locator = card.locator(".visiting .touchingPort > div")

        for i in range(port_locator.count()):
            text = port_locator.nth(i).inner_text().strip()
            if text and text != "•":
                visiting_ports.append(text)

        return visiting_ports

    def _go_to_next_page(self, page) -> bool:
        next_button = self._get_next_button(page)

        if next_button.count() == 0:
            logger.info("No next-page button found")
            return False

        if next_button.get_attribute("aria-disabled") == "true" or next_button.is_disabled():
            return False

        first_card = page.locator(".cruiseCard").first
        first_card_id_before = first_card.get_attribute("data-automation-cruise-id")

        logger.info("➡️ Moving to next page...")
        next_button.click()
        page.wait_for_timeout(2000)

        if first_card_id_before:
            page.wait_for_function(
                """
                prevId => {
                    const firstCard = document.querySelector('.cruiseCard');
                    return (
                        firstCard &&
                        firstCard.getAttribute('data-automation-cruise-id') !== prevId
                    );
                }
                """,
                arg=first_card_id_before,
                timeout=15_000,
            )
        else:
            page.wait_for_selector(".cruiseCard", timeout=15000)

        return True

    def _get_next_button(self, page):
        return page.locator('button[aria-label="pagination button next"]')

    def _extract_cruise_from_card(self, card) -> Dict:
        cruise_id = card.get_attribute("data-automation-cruise-id") or ""
        scraped_at = datetime.utcnow().isoformat() + "Z"

        nights_text = card.locator(".nights").inner_text().strip()
        try:
            ship_name = card.locator(".longshipname").inner_text().strip()
        except Exception:
            logger.info(f"❗️ Ship name not found for cruise {cruise_id}")
            ship_name = "MSC Undefined"
        name = card.locator(".cruiseTitle").inner_text().strip()

        departure_port = ""
        departure_port_locator = card.locator(".roundtrip .touchingPort div")
        if departure_port_locator.count() > 0:
            departure_port = departure_port_locator.first.inner_text().strip()

        details_link_locator = card.locator(".ctaItinerary a.cmp-button")
        product_link = ""
        if details_link_locator.count() > 0:
            product_link = details_link_locator.first.get_attribute("href") or ""

        if product_link.startswith("/"):
            product_link = f"{self.base_url}{product_link}"

        nights = None
        try:
            nights = int(nights_text.split()[0])
        except Exception:
            pass

        return {
            "scraped_at": scraped_at,
            "id": cruise_id,
            "ship_code": "",
            "destination_code": "",
            "package_code": "",
            "product_link": product_link,
            "name": name,
            "ship_name": ship_name,
            "nights_text": nights_text,
            "departure_port": departure_port,
            "view_dates_button_id": "",
            "nights": nights,
            "visiting_ports": self._extract_visiting_ports(card),
            "sailings": [],
        }

    def _extract_numeric_price(self, text: str) -> str:
        digits = "".join(ch for ch in text if ch.isdigit())
        return digits

    def _map_room_type_to_field(self, room_type_text: str) -> Optional[str]:
        return re.sub(r"\s+", "_", room_type_text.strip().lower()) or None

    def _extract_cheapest_sailing_for_room_type(
        self, page, room_tab, cruise: Dict, cruise_details_url
    ) -> Optional[Dict]:
        room_tab.click()
        page.wait_for_timeout(1000)
        url = cruise_details_url

        if not url:
            url = page.url

        room_type_text = room_tab.locator(".macrocategory__cabinType").inner_text().strip()
        room_key = self._map_room_type_to_field(room_type_text)

        if not room_key:
            return None

        room_price_text = room_tab.locator(".macrocategory__subtext").inner_text().strip()
        room_price = self._extract_numeric_price(room_price_text)

        dateline = page.locator(".cabinListBreakpoint .algolia-analytics").first
        if dateline.count() == 0:
            return None

        date_locator = dateline.locator(".dateline__dates")
        if date_locator.count() == 0:
            return None

        date_text = date_locator.first.inner_text().strip()

        timestamp, date_range = self._parse_msc_date_range(date_text)
        if not timestamp:
            return None

        sailing = {
            "sailing_id": f"{cruise['id']}-{timestamp}",
            "sailing_url": url,
            "timestamp": timestamp,
            "date_range": date_range,
            "base_price": room_price,
            room_key: room_price,
        }

        return sailing

    def _extract_sailings_for_cruise(self, page, cruise_card, cruise: Dict) -> List[Dict]:
        sailings = []

        view_dates_button = cruise_card.locator("button.cmp-button", has_text="date")
        cruise_details_url = ""
        details_link = cruise_card.locator(".ctaItinerary a.cmp-button")
        if details_link.count() > 0:
            cruise_details_url = details_link.first.get_attribute("href") or ""
            if cruise_details_url.startswith("/"):
                cruise_details_url = f"{self.base_url}{cruise_details_url}"
        if view_dates_button.count() == 0:
            return sailings

        view_dates_button.first.click()
        page.wait_for_timeout(2000)

        room_types = page.locator(".macrocategory")
        room_count = room_types.count()

        for i in range(room_count):
            room_tab = room_types.nth(i)
            sailing = self._extract_cheapest_sailing_for_room_type(
                page, room_tab, cruise, cruise_details_url
            )
            if sailing:
                sailings.append(sailing)

        close_button = page.locator('button:has(i[aria-label="Close layer"])')
        if close_button.count() > 0:
            close_button.first.click()
            page.wait_for_timeout(1000)

        return sailings

    def _sort_results_by_price(self, page) -> None:
        logger.info("📥 Sorting MSC cruise results by cheapest sailing price...")

        open_button = (
            page.locator(".cmp-sorting__parentDiv")
            .filter(has_text="Sort by:")
            .locator(".cmp-sorting__iconDownContainer")
        )
        if not open_button.count():
            logger.warning("⚠️ Sort dropdown open button not found, skipping sort.")
            return

        open_button.click()

        dropdown_list = page.locator(".cmp-sorting__dropdownListInner")
        try:
            dropdown_list.wait_for(state="visible", timeout=5000)
        except Exception:
            logger.warning("⚠️ Sort dropdown list did not become visible, skipping sort.")
            return

        price_option = page.locator(".cmp-sorting__dropdownListItem", has_text="Price")
        if not price_option.count():
            logger.warning("⚠️ 'Price' option not found in sort dropdown, skipping sort.")
            return

        price_option.click()

        try:
            page.wait_for_load_state("networkidle", timeout=15000)
            page.wait_for_selector(".cruiseCard", state="visible", timeout=15000)
        except Exception:
            logger.warning("⚠️ Timed out waiting for cruise cards to reload after sort.")

    def _load_all_cruises(
        self,
        page,
        max_cruises: Optional[int] = None,
        max_sailings: Optional[int] = None,
    ) -> List[Dict]:
        page.wait_for_selector(".cruiseCard", timeout=15000)

        cruises = []
        seen_ids = set()

        logger.info("📥 Loading MSC cruises...")
        self._sort_results_by_price(page)
        cruise_count = 1
        while max_cruises is None or len(cruises) < max_cruises:
            cards = page.locator(".cruiseCard")
            count = cards.count()

            for i in range(count):
                if max_cruises:
                    logger.info(f"   Processing Cruise: {cruise_count}/{max_cruises}")
                else:
                    logger.info(f"   Processing Cruise: {cruise_count}")

                card = cards.nth(i)
                cruise_id = card.get_attribute("data-automation-cruise-id")

                if not cruise_id or cruise_id in seen_ids:
                    continue

                cruise = self._extract_cruise_from_card(card)
                cruise["sailings"] = self._extract_sailings_for_cruise(page, card, cruise)
                cruises.append(cruise)
                seen_ids.add(cruise_id)
                cruise_count += 1

                if max_cruises is not None and len(cruises) >= max_cruises:
                    logger.info(f"✔️ Reached max cruise limit: {max_cruises}")
                    return cruises

            moved = self._go_to_next_page(page)
            if not moved:
                logger.info("✔️ Reached last MSC results page")
                break

        logger.info(f"✔️ Successfully extracted {len(cruises)} MSC cruises")
        return cruises

    def _process_cruise_data(self, raw_data: dict) -> dict:
        logger.info("🧹 Writing processed cruise json file")
        processed_cruises = []

        for cruise in raw_data.get("cruises", []):
            ship_name = cruise.get("ship_name", "")
            ship_code = "-".join(ship_name.split()) if ship_name else ""

            departure = cruise.get("departure_port", "")
            visiting = cruise.get("visiting_ports", [])
            ports = ([departure] + visiting + [departure]) if departure else visiting

            sailings = []
            for s in cruise.get("sailings", []):
                sailing = {
                    "sailing_id": s.get("sailing_id"),
                    "timestamp": s.get("timestamp"),
                    "date_range": s.get("date_range"),
                    "base_price": s.get("base_price"),
                }
                cabin_keys = [
                    k
                    for k in s
                    if k
                    not in ("sailing_id", "sailing_url", "timestamp", "date_range", "base_price")
                ]
                for key in cabin_keys:
                    try:
                        sailing[key] = int(s[key])
                    except (ValueError, TypeError):
                        sailing[key] = s[key]
                sailings.append(sailing)

            cruise_id = cruise.get("id", "")
            processed_cruises.append(
                {
                    "id": cruise_id,
                    "name": cruise.get("name"),
                    "nights": cruise.get("nights"),
                    "ship": {
                        "name": ship_name,
                        "code": ship_code,
                    },
                    "sailings": sailings,
                    "route": {
                        "departure": departure,
                        "destination_code": cruise.get("destination_code") or departure,
                        "ports": ports,
                    },
                    "metadata": {
                        "package_code": cruise.get("package_code") or cruise_id,
                        "link": cruise.get("product_link"),
                        "scraped_at": cruise.get("scraped_at"),
                    },
                }
            )

        return {
            "timestamp": datetime.now().isoformat(),
            "source_url": raw_data.get("url"),
            "total_found": raw_data.get("count", 0),
            "total_processed": len(processed_cruises),
            "cruises": processed_cruises,
        }
