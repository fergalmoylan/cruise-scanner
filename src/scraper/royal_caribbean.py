#!/usr/bin/env python3

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from playwright.sync_api import sync_playwright


class RoyalCaribbeanOptimizedScraper:
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.base_url = "https://www.royalcaribbean.com/gbr/en"
        self.cruises_url = f"{self.base_url}/cruises?search=nights:6~8,9~11,gte12|ship:IC,LE,OA,ST,SY,UT,WN|startDate:2026-01-01~2026-01-31,2026-02-01~2026-02-28,2026-03-01~2026-03-31,2026-04-01~2026-04-30,2027-01-01~2027-01-31,2027-02-01~2027-02-28,2027-03-01~2027-03-31,2027-04-01~2027-04-30&country=IRL&market=gbr&language=en"
        self.data_dir = Path("data")
        self.raw_dir = self.data_dir / "raw"
        self.processed_dir = self.data_dir / "processed"

        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)

    def scrape(self, max_cruises: Optional[int] = None) -> List[Dict]:
        print("🚢 Starting Royal Caribbean scraper...")
        print(f"📍 URL: {self.cruises_url}")
        print(f"   Mode: {'Headless' if self.headless else 'Visible'}")
        if max_cruises:
            print(f"   Max cruises: {max_cruises}")

        with sync_playwright() as p:
            browser = p.webkit.launch(headless=self.headless)
            context = browser.new_context(viewport={"width": 1920, "height": 1080})
            page = context.new_page()

            try:
                print("📡 Loading page...")
                page.goto(self.cruises_url, wait_until="domcontentloaded", timeout=30000)

                print("⏳ Waiting for cruise cards...")
                page.wait_for_selector('[data-testid*="cruise-card-container"]', timeout=15000)
                page.wait_for_timeout(2000)
                self._handle_cookie_consent(page)

                all_cruises = self._load_all_cruises(page, max_cruises)

                print(f"✅ Extracted {len(all_cruises)} cruises")

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

                print(f"💾 Saved to {output_file}")

                cleaned_data = self._process_cruise_data(all_cruises)
                if cleaned_data:
                    cleaned_file = self.processed_dir / f"cruises_cleaned_{timestamp}.json"
                    with open(cleaned_file, "w", encoding="utf-8") as f:
                        json.dump(cleaned_data, f, indent=2, ensure_ascii=False)
                    print(f"💾 Saved cleaned data to {cleaned_file}")

                return all_cruises

            except Exception as e:
                print(f"❌ Error during scraping: {e}")
                import traceback

                traceback.print_exc()
                return []

            finally:
                browser.close()

    def _handle_cookie_consent(self, page):
        print("🍪 Checking for cookie consent...")
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
                print(f"  ✓ {cookie_result['action'].title()} cookies: '{cookie_result['text']}'")
                page.wait_for_timeout(1000)
            else:
                print("  ℹ️ No cookie banner found")

        except Exception as e:
            print(f"  ⚠️ Error handling cookies: {e}")

    def _load_all_cruises(self, page, max_cruises: Optional[int]) -> List[Dict]:
        all_cruises = []
        load_more_count = 0
        while True:
            print(f"🔍 Extracting batch {load_more_count + 1}...")
            # todo bug here , it keeps scraping all cruises from the start on each iteration
            current_cruises = self._extract_cruises_from_page(page)

            for cruise in current_cruises:
                cruise_id = cruise.get("id")
                if cruise_id and not any(c.get("id") == cruise_id for c in all_cruises):
                    all_cruises.append(cruise)

            print(f"  Found {len(current_cruises)} cruises (Total: {len(all_cruises)})")

            if max_cruises and len(all_cruises) >= max_cruises:
                print(f"  ✓ Reached max cruises limit ({max_cruises})")
                return all_cruises[:max_cruises]

            load_more_clicked = self._click_load_more(page)

            if not load_more_clicked:
                print("  ✓ No more cruises to load")
                break

            load_more_count += 1

            print("  ⏳ Waiting for new cruises to load...")
            page.wait_for_timeout(3000)

            if load_more_count > 100:
                print("  ⚠️ Reached maximum load iterations")
                break

        return all_cruises

    def _click_load_more(self, page) -> bool:
        try:
            print("Trying to load more results")
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

            print(f"JS result: {result}")
            if result and result.get("found"):
                print("✓ Clicked button via JavaScript")
                return True
            else:
                print("ℹ️ Load more button not found/visible.")
                return False

        except Exception as e:
            print(f"ℹ️ Load More click failed: {e}")
            return False

    def _extract_cruises_from_page(self, page) -> List[Dict]:
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

            try:
                print(
                    f"Processing cruise {i + 1}/{len(basic_cruises)}: {cruise.get('name', 'Unknown')}"
                )

                view_dates_button = page.locator(
                    f'[data-testid="{cruise["view_dates_button_id"]}"]'
                )
                time.sleep(2)
                view_dates_button.click()

                page.wait_for_timeout(3000)
                time.sleep(2)

                cruise["sailings"] = self._extract_sailing_dates_and_prices(page)
                print("Processed cruise sailings:", cruise["sailings"])

                try:
                    close_button = page.locator("#cruise-detail-close-button")
                    if close_button.is_visible(timeout=1000):
                        close_button.click()
                        print("  ✓ Closed modal")
                    else:
                        page.keyboard.press("Escape")
                        print("  ✓ Closed modal with Escape")

                    page.wait_for_timeout(1000)

                except Exception as e:
                    print(f"  ⚠️ Failed to close modal: {e}")
                    page.keyboard.press("Escape")
                    page.wait_for_timeout(1000)

            except Exception as e:
                print(f"  ⚠️ Failed to get pricing for cruise {cruise.get('id')}: {e}")
                cruise["sailings"] = []

            cruises_with_pricing.append(cruise)

        return cruises_with_pricing

    def _extract_sailing_dates_and_prices(self, page) -> List[Dict]:
        print("Extracting sailing dates and prices")

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

        # todo
        # need to extract the year also, so should use this element
        # <div class="RefinedCruiseCarousel-styles__RefinedCruiseCarouselActiveMonthLabel-sc-cbb0e067-5 cFXhvS">Saturday 22 Aug  - Saturday 29 Aug 2026</div>

        for date_info in date_options:
            try:
                date_tabs = page.locator('[role="tab"]')
                if date_tabs.count() == 0:
                    date_tabs = page.locator(f'li:has-text("{date_info["date_range"]}")')

                if date_info["element_index"] < date_tabs.count():
                    date_tabs.nth(date_info["element_index"]).click()
                    page.wait_for_timeout(1000)
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

                    all_sailings.append(
                        {
                            "date_range": date_info["date_range"],
                            "base_price": date_info["base_price"],
                            "room_prices": room_prices,
                        }
                    )

            except Exception as e:
                print(f"    ⚠️ Failed to get prices for date {date_info['date_range']}: {e}")

        return all_sailings

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
                "sailings": [
                    {
                        "date": sailing.get("date_range", ""),
                        "interior": sailing.get("room_prices", {"interior": 0}).get("interior"),
                        "ocean_view": sailing.get("room_prices", {"ocean_view": 0}).get(
                            "ocean_view"
                        ),
                        "balcony": sailing.get("room_prices", {"balcony": 0}).get("balcony"),
                        "suite": sailing.get("room_prices", {"suite": 0}).get("suite"),
                    }
                    for sailing in cruise.get("sailings", [])
                ],
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
            print(f"Invalid max_cruises value: {sys.argv[1]}")

    scraper = RoyalCaribbeanOptimizedScraper(headless=False)
    cruises = scraper.scrape(max_cruises=max_cruises)

    if cruises:
        print(f"\n✅ Successfully scraped {len(cruises)} cruises")
        print("Check data/raw/ and data/processed/ for results")
    else:
        print("\n❌ No cruises found")


if __name__ == "__main__":
    main()
