#!/usr/bin/env python3
from __future__ import annotations

import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union

from playwright.sync_api import sync_playwright

LAST_SAILING_YEAR: int | None = None

logger = logging.getLogger(__name__)


class RoyalCaribbeanOptimizedScraper:
    def __init__(self, headless: bool = True):
        self.context = None
        self.headless = headless
        self.base_url = "https://www.royalcaribbean.com/gbr/en"
        self.cruises_url = f"{self.base_url}/cruises?search=departurePort:BCN,BYE,FLL,LAX,MIA,ROM,SIN,YOK|nights:6~8,9~11,gte12|ship:AL,AN,HM,IC,LE,OA,OV,OY,QN,ST,SY,UT,WN&country=IRL&market=gbr&language=en"
        self.data_dir = Path("data")
        self.raw_dir = self.data_dir / "raw"
        self.processed_dir = self.data_dir / "processed"

        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)

    def scrape(
        self, max_cruises: Optional[int] = None, max_sailings: Optional[int] = None
    ) -> tuple[List[Dict], str]:
        logger.info("🚢 Starting Royal Caribbean scraper...")
        logger.info(f"📍 URL: {self.cruises_url}")
        logger.info(f"   Mode: {'Headless' if self.headless else 'Visible'}")
        if max_cruises:
            logger.info(f"   Max cruises: {max_cruises}")
        if max_cruises:
            logger.info(f"   Max sailings per cruise: {max_sailings}")

        with sync_playwright() as p:
            browser = p.webkit.launch(headless=self.headless)
            self.context = browser.new_context(viewport={"width": 1920, "height": 1080})
            page = self.context.new_page()

            try:
                logger.info("📡 Loading page...")
                page.goto(self.cruises_url, wait_until="domcontentloaded", timeout=30000)

                logger.info("⏳ Waiting for cruise cards...")
                page.wait_for_selector('[data-testid*="cruise-card-container"]', timeout=15000)
                page.wait_for_timeout(2000)
                self._handle_cookie_consent(page)

                all_cruises = self._load_all_cruises(page, max_cruises, max_sailings)

                logger.info(f"✅ Extracted {len(all_cruises)} cruises")

                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = self.raw_dir / f"cruises_optimized_{timestamp}.json"

                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(
                        {
                            "timestamp": timestamp,
                            "url": self.cruises_url,
                            "count": len(all_cruises),
                            "cruises": all_cruises,
                        },
                        f,
                        indent=2,
                        ensure_ascii=False,
                    )

                logger.info(f"💾 Saved Raw JSON to {output_file}")

                cleaned_data = self._process_cruise_data(all_cruises)
                if cleaned_data:
                    cleaned_file = self.processed_dir / f"cruises_cleaned_{timestamp}.json"
                    with open(cleaned_file, "w", encoding="utf-8") as f:
                        json.dump(cleaned_data, f, indent=2, ensure_ascii=False)
                    logger.info(f"💾 Saved cleaned data to {cleaned_file}")

                return all_cruises, str(cleaned_file)

            except Exception as e:
                logger.info(f"❌ Error during scraping: {e}")
                import traceback

                traceback.logger.info_exc()
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
                    f"🚫 {cookie_result['action'].title()} cookies: '{cookie_result['text']}'"
                )
                page.wait_for_timeout(1000)
            else:
                logger.info("  ℹ️ No cookie banner found")

        except Exception as e:
            logger.info(f"  ⚠️ Error handling cookies: {e}")

    def _format_to_snake_case(self, text: str) -> str:
        import re

        text = re.sub(r"[^\w\s]", "", text)
        text = re.sub(r"\s+", "_", text.strip())
        return text.lower()

    def _extract_suite_details(self, page) -> Dict[str, str]:
        try:
            page.wait_for_selector('[class*="RoomSubtypePanel_subtypesList"]', timeout=10000)

            suite_details = page.evaluate("""() => {
                const suites = {};
                const suiteCards = document.querySelectorAll('[class*="RoomSubtypePanel_subtypesList"] > li');

                suiteCards.forEach(card => {
                    const nameEl = card.querySelector('[data-stateroom-subtype-name="true"], [data-testid="card-title"]');
                    const priceEl = card.querySelector('[data-testid="main-price-amount"]');

                    if (nameEl && priceEl) {
                        const name = nameEl.innerText.trim();
                        const price = priceEl.innerText.trim();
                        suites[name] = price;
                    }
                });

                return suites;
            }""")

            formatted_suites = {}
            for suite_name, price in suite_details.items():
                key = self._format_to_snake_case(suite_name)
                formatted_suites[key] = price

            return formatted_suites

        except Exception as e:
            logger.info(f"    ⚠️ Failed to extract suite details: {e}")
            return {}

    def _parse_sailing_date(self, date_text: str) -> Union[tuple[str, str], tuple[None, str]]:
        import re
        from datetime import datetime

        global LAST_SAILING_YEAR

        date_text = date_text.replace("\u00a0", " ").strip()
        logger.info("    📆 Parsing sailing date:", date_text)

        pattern = (
            r"(?:\w+day),?\s+(\d{1,2})\s+([A-Za-z]+)(?:\s+(\d{4}))?"  # start: day, month, optional year
            r"\s*-\s*"
            r"(?:\w+day),?\s+(\d{1,2})\s+([A-Za-z]+)(?:\s+(\d{4}))?"  # end: day, month, optional year
            r"$"
        )
        match = re.search(pattern, date_text)
        if not match:
            logger.info("   ⚠️No match found for date pattern:", date_text)
            return None, date_text

        start_day, start_month, start_year_str, end_day, end_month, end_year_str = match.groups()

        months = {
            "Jan": 1,
            "Feb": 2,
            "Mar": 3,
            "Apr": 4,
            "May": 5,
            "Jun": 6,
            "Jul": 7,
            "Aug": 8,
            "Sep": 9,
            "Oct": 10,
            "Nov": 11,
            "Dec": 12,
        }
        sm = months.get(start_month[:3], 1)
        em = months.get(end_month[:3], 1)
        sd = int(start_day)
        ed = int(end_day)

        start_year = int(start_year_str) if start_year_str else None
        end_year = int(end_year_str) if end_year_str else None

        if start_year is not None:
            year = start_year
        elif end_year is not None:
            crosses_year = (em < sm) or (em == sm and ed < sd)
            year = end_year - 1 if crosses_year else end_year
        elif LAST_SAILING_YEAR is not None:
            year = LAST_SAILING_YEAR
        else:
            year = datetime.now().year

        LAST_SAILING_YEAR = year

        start_date = f"{year:04d}-{sm:02d}-{sd:02d}"
        date_range = f"{start_month} {start_day} - {end_month} {end_day}, {year}"
        return start_date, date_range

    def _load_all_cruises(
        self, page, max_cruises: Optional[int], max_sailings: Optional[int]
    ) -> List[Dict]:
        load_more_count = 0
        logger.info("📥 Loading all cruises...")

        while True:
            if max_cruises:
                current_count = page.evaluate("""() => {
                    return document.querySelectorAll('[data-testid*="cruise-card"]').length;
                }""")
                if current_count >= max_cruises:
                    logger.info(f"✅ Reached max cruise limit: {max_cruises}")
                    break

            load_more_clicked = self._click_load_more(page)

            if not load_more_clicked:
                logger.info(f"✅ All cruises loaded (clicked 'Load More' {load_more_count} times)")
                break

            load_more_count += 1
            logger.info(f"  ⏳ Clicked 'Load More' #{load_more_count}, waiting for new cruises...")

            page.wait_for_timeout(2000)

        logger.info("🔍 Extracting all cruises from page...")
        all_cruises = self._extract_cruises_from_page(page, max_cruises, max_sailings)

        if max_cruises and len(all_cruises) > max_cruises:
            all_cruises = all_cruises[:max_cruises]

        logger.info(f"✅ Successfully extracted {len(all_cruises)} cruises")
        return all_cruises

    def _click_load_more(self, page) -> bool:
        try:
            result = page.evaluate("""() => {
                const isVisible = (el) => {
                    const rect = el.getBoundingClientRect();
                    const style = window.getComputedStyle(el);
                    return (
                        rect.width > 0 && rect.height > 0 &&
                        style.visibility !== 'hidden' &&
                        style.display !== 'none'
                    );
                };

                const btn = document.querySelector('button[data-testid="load-more-button"]');
                if (btn && isVisible(btn) && !btn.disabled) {
                    btn.click();
                    return { found: true, text: btn.innerText || btn.textContent || '' , clicked: true };
                }
                return { found: false };
            }""")

            if result and result.get("found"):
                return True
            else:
                return False

        except Exception:
            return False

    def _extract_cruises_from_page(
        self, page, max_cruises: Optional[int], max_sailings: Optional[int]
    ) -> List[Dict]:
        basic_cruises = page.evaluate("""() => {
            const cruises = [];
            const cards = document.querySelectorAll('[data-testid*="cruise-card-container"]');

            Array.from(cards).forEach((card) => {
                const cruise = {
                    scraped_at: new Date().toISOString(),
                    id: card.getAttribute('data-group-id') || card.id,
                    ship_code: card.getAttribute('data-ship-code'),
                    destination_code: card.getAttribute('data-destination-code'),
                    package_code: card.getAttribute('data-package-code'),
                    product_link: card.getAttribute('data-product-view-link'),

                    name: card.querySelector('[data-testid*="cruise-name-label"]')?.innerText,
                    ship_name: card.querySelector('[data-testid*="cruise-ship-label"]')?.innerText,
                    nights_text: card.querySelector('[data-testid*="cruise-duration-label"]')?.innerText,
                    departure_port: card.querySelector('[data-testid*="cruise-roundtrip-label"] span:nth-child(2)')?.innerText,

                    view_dates_button_id: card.querySelector('[data-testid*="cruise-view-dates-button"]')?.getAttribute('data-testid')
                };

                const nightsMatch = (cruise.nights_text || '').match(/(\\d+)\\s*Night/i);
                if (nightsMatch) cruise.nights = parseInt(nightsMatch[1]);

                const portItems = card.querySelectorAll('[data-testid*="cruise-ports-label"] li');
                cruise.visiting_ports = Array.from(portItems).map(li => li.innerText);

                cruises.push(cruise);
            });

            return cruises;
        }""")

        cruises_with_pricing = []

        for i, cruise in enumerate(basic_cruises):
            if not cruise.get("view_dates_button_id"):
                cruises_with_pricing.append(cruise)
                continue

            if max_cruises and i >= max_cruises:
                logger.info("    ☑️ Processed all cruises")
                break

            try:
                if max_cruises:
                    logger.info(
                        f"Processing cruise {i + 1}/{max_cruises}: {cruise.get('name', 'Unknown')}"
                    )

                else:
                    logger.info(
                        f"Processing cruise {i + 1}/{len(basic_cruises)}: {cruise.get('name', 'Unknown')}"
                    )
                try:
                    self._click_load_more(page)
                except Exception:
                    continue

                view_dates_button = page.locator(
                    f'[data-testid="{cruise["view_dates_button_id"]}"]'
                ).first

                time.sleep(5)
                view_dates_button.click()

                page.wait_for_timeout(5000)

                cruise["sailings"] = self._extract_sailing_dates_and_prices(
                    page, self.context, cruise["id"], max_sailings
                )

                try:
                    close_button = page.locator("#cruise-detail-close-button")
                    if close_button.is_visible(timeout=1000):
                        close_button.click()
                    else:
                        page.keyboard.press("Escape")

                    page.wait_for_timeout(1000)

                except Exception as e:
                    logger.info(f"  ⚠️ Failed to close modal: {e}")
                    page.keyboard.press("Escape")
                    page.wait_for_timeout(1000)

            except Exception as e:
                logger.info(f"  ⚠️ Failed to get pricing for cruise {cruise.get('id')}: {e}")
                cruise["sailings"] = []

            cruises_with_pricing.append(cruise)

        return cruises_with_pricing

    def _extract_sailing_dates_and_prices(
        self, page, context, id, max_sailings: Optional[int]
    ) -> List[Dict]:
        logger.info("    📊 Extracting sailing dates and prices...")
        all_sailings = []

        date_options = page.evaluate("""() => {
                const dates = [];
                let dateElements = document.querySelectorAll('[role="tab"]');
                if (dateElements.length === 0) {
                    const allElements = document.querySelectorAll('li, div[class*="Tab"], div[class*="tab"]');
                    dateElements = Array.from(allElements).filter(el => {
                        const text = el.innerText || '';
                        return /[A-Z][a-z]{2}\\s+\\d+\\s*-\\s*[A-Z][a-z]{2}\\s+\\d+/.test(text);
                    });
                }

                dateElements.forEach(el => {
                    const fullText = el.innerText || '';
                    const dateMatch = fullText.match(/([A-Z][a-z]{2}\\s+\\d+\\s*-\\s*[A-Z][a-z]{2}\\s+\\d+)/);
                    const priceMatch = fullText.match(/[€£$]\\s*[\\d,]+/);
                    if (dateMatch) {
                        dates.push({
                            date_range: dateMatch[1],
                            base_price: priceMatch ? priceMatch[0] : null,
                            element_index: dates.length
                        });
                    }
                });
                return dates;
            }""")
        if max_sailings:
            date_options = date_options[:max_sailings]
        for date_info in date_options:
            try:
                date_tabs = page.locator('[role="tab"]')
                if date_tabs.count() == 0:
                    date_tabs = page.locator(f'li:has-text("{date_info["date_range"]}")')

                if date_info["element_index"] < date_tabs.count():
                    date_tabs.nth(date_info["element_index"]).click()
                    page.wait_for_timeout(5000)
                    full_date = page.evaluate("""() => {
                        const activeLabel = document.querySelector('[class*="RefinedCruiseCarouselActiveMonthLabel"]');
                        return activeLabel ? activeLabel.innerText : null;
                    }""")
                    room_prices = page.evaluate("""() => {
                            const prices = {}
                            const roomTypes = {
                                'interior': 'INTERIOR',
                                'ocean_view': 'OUTSIDE',
                                'balcony': 'BALCONY',
                                'suite': 'DELUXE'
                            };
                            for (const [key, testId] of Object.entries(roomTypes)) {
                                const container = document.querySelector(`[data-testid="room-view-card-container-${testId}"]`);
                                if (container) {
                                    let priceText = '';
                                    let currencyText = '';
                                    const priceElements = container.querySelectorAll('[class*="Price"], [class*="price"]');
                                    for (const el of priceElements) {
                                        const text = el.innerText || '';
                                        if (/^[€£$]/.test(text)) {
                                            currencyText = text;
                                        } else if (/^\\d+/.test(text)) {
                                            priceText = text;
                                        }
                                    }
                                    if (!priceText) {
                                        const allText = container.innerText || '';
                                        const match = allText.match(/([€£$])\\s*([\\d,]+)/);
                                        if (match) {
                                            currencyText = match[1];
                                            priceText = match[2];
                                        }
                                    }
                                    if (priceText) {
                                        prices[key] = currencyText + priceText;
                                    }
                                }
                            }
                            return prices;
                        }""")

                    logger.info("    ⬇️ Extracted full date:", full_date)

                    room_prices = {k: int(v.replace("€", "")) for k, v in room_prices.items()}
                    start_date, date_range = (
                        self._parse_sailing_date(full_date)
                        if full_date
                        else (None, date_info["date_range"])
                    )

                    logger.info("    ❗️ Got sailing date:", start_date, date_range)

                    suite_details = {}
                    if room_prices.get("suite"):
                        suite_details = self._extract_suite_details_in_new_tab(page, context)

                    sailing_data = {
                        "sailing_id": "{}-{}".format(id, start_date),
                        "timestamp": start_date,
                        "date_range": date_range,
                        "base_price": date_info["base_price"].replace("€", ""),
                        **room_prices,
                    }

                    if suite_details:
                        if "suite" in sailing_data:
                            sailing_data["suite_guarantee"] = sailing_data.pop("suite")
                        sailing_data.update(suite_details)

                    all_sailings.append(sailing_data)

            except Exception as e:
                logger.info(f"    ⚠️ Failed to get prices for date {date_info['date_range']}: {e}")

        return all_sailings

    def _extract_suite_details_in_new_tab(self, page, context) -> Dict[str, str]:
        logger.info("    📦 Fetching suite details in new tab...")
        suite_details = {}
        new_page = None

        try:
            time.sleep(5)
            page.wait_for_timeout(5000)
            suite_button = page.locator('[data-testid="book-now-button-DELUXE"]')
            if suite_button.count() == 0:
                logger.info("    ⛔️'Book Suite' button not found.")
                return {}

            logger.info("    📂️ Opening new tab...")
            with context.expect_page(timeout=5000) as new_page_info:
                page.evaluate("window.open(window.location.href, '_blank')")

            new_page = new_page_info.value
            time.sleep(5)
            new_page.wait_for_timeout(5000)
            new_page_suite_button = new_page.locator('[data-testid="book-now-button-DELUXE"]')
            if new_page_suite_button.count() == 0:
                logger.info("    ⛔️'Book Suite' button not found in new page.")
                return {}
            is_disabled = new_page_suite_button.evaluate("el => el.disabled")
            if is_disabled:
                logger.info("    ℹ️ Suite unavailable (button disabled)")
                return {}
            new_page.locator('[data-testid="book-now-button-DELUXE"]').click(modifiers=["Meta"])
            new_page.wait_for_timeout(5000)
            new_page.wait_for_load_state("networkidle")
            room_selection_btn = new_page.locator('[data-testid="funnel-footer-cta-btn"]')
            room_selection_btn.wait_for(timeout=10000)
            room_selection_btn.click()

            new_page.wait_for_load_state("networkidle", timeout=15000)

            new_page.wait_for_selector('[class*="RoomSubtypePanel_subtypesList"]', timeout=10000)

            suite_data = new_page.evaluate("""() => {
                const suites = {};
                const suiteCards = document.querySelectorAll('[class*="RoomSubtypePanel_subtypesList"] > li');

                suiteCards.forEach(card => {
                    const nameEl = card.querySelector('[data-stateroom-subtype-name="true"], [data-testid="card-title"]');
                    const priceEl = card.querySelector('[data-testid="main-price-amount"]');

                    if (nameEl && priceEl) {
                        const name = nameEl.innerText.trim();
                        const price = priceEl.innerText.trim();
                        suites[name] = price;
                    }
                });
                return suites;
            }""")

            for suite_name, price in suite_data.items():
                key = self._format_to_snake_case(suite_name)
                suite_details[key] = int(price.replace("€", "").replace(".", "").strip())

        except Exception as e:
            logger.info(f"    ⚠️ Failed to get suite details: {e}")

        finally:
            if new_page:
                try:
                    new_page.close()
                except Exception as e:
                    logger.info(f"    ⚠️ Failed to close page: {e}")
                    pass

        return suite_details

    def _process_cruise_data(self, raw_data: List[Dict]) -> Dict:
        cleaned_cruises = []

        for cruise in raw_data:
            if cruise.get("error"):
                continue

            cleaned = {
                "id": cruise.get("id", ""),
                "name": cruise.get("name", ""),
                "nights": cruise.get("nights", ""),
                "ship": {
                    "name": cruise.get("ship_name", ""),
                    "code": cruise.get("ship_code", ""),
                },
                "sailings": cruise.get("sailings", []),
                "route": {
                    "departure": cruise.get("departure_port", ""),
                    "destination_code": cruise.get("destination_code", ""),
                    "ports": cruise.get("visiting_ports", []),
                },
                "metadata": {
                    "package_code": cruise.get("package_code", ""),
                    "link": cruise.get("product_link", ""),
                    "scraped_at": cruise.get("scraped_at", ""),
                },
            }

            if cleaned["name"] or cleaned["ship"]["name"]:
                cleaned_cruises.append(cleaned)

        return {
            "timestamp": datetime.now().isoformat(),
            "source_url": self.cruises_url,
            "total_found": len(raw_data),
            "total_processed": len(cleaned_cruises),
            "cruises": cleaned_cruises,
        }


def main():
    import sys

    max_cruises = None
    if len(sys.argv) > 1:
        try:
            max_cruises = int(sys.argv[1])
        except ValueError:
            logger.info(f"Invalid max_cruises value: {sys.argv[1]}")

    scraper = RoyalCaribbeanOptimizedScraper(headless=True)
    cruises, _ = scraper.scrape(max_cruises=max_cruises)

    if cruises:
        logger.info(f"\n✅ Successfully scraped {len(cruises)} cruises")
        logger.info("Check data/raw/ and data/processed/ for results")
    else:
        logger.info("\n❌ No cruises found")


if __name__ == "__main__":
    main()
