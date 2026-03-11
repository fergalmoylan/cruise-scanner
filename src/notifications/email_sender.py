from __future__ import annotations

import logging
import os
import smtplib
import ssl
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path
from typing import List

from dotenv import load_dotenv

from .html_builder import _parse_price_to_float, build_html_email, read_latest_scrape_rows

log = logging.getLogger(__name__)

load_dotenv()


def _ordinal(n: int) -> str:
    if 11 <= (n % 100) <= 13:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def _format_subject_date(scrape_timestamp_raw: str) -> str:
    s = (scrape_timestamp_raw or "").strip()
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    dt = datetime.fromisoformat(s)
    return f"{dt.strftime('%B')} {_ordinal(dt.day)} {dt.year}"


def _get_env(name: str, required: bool = True) -> str:
    val = (os.environ.get(name) or "").strip()
    if required and not val:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return val


def _parse_recipients(raw: str) -> List[str]:
    return [r.strip() for r in raw.split(",") if r.strip()]


def send_mail_html(
    html: str,
    subject: str,
    recipients: List[str],
    sender_address: str,
    sender_password: str,
    smtp_host: str = "smtp.gmail.com",
    smtp_port: int = 465,
) -> None:
    em = EmailMessage()
    em["From"] = sender_address
    em["To"] = ", ".join(recipients)
    em["Subject"] = subject
    em.set_content("This is an HTML email. Please view it in an HTML-compatible email client.")
    em.add_alternative(html, subtype="html")

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(smtp_host, smtp_port, context=context) as smtp:
        smtp.login(sender_address, sender_password)
        smtp.send_message(em)

    log.info("Mail sent successfully")


def main() -> None:
    logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"))

    sender_address = _get_env("SENDER_ADDRESS")
    sender_password = _get_env("SENDER_PASSWORD")
    recipients = _parse_recipients(_get_env("RECIPIENTS"))

    rcc = read_latest_scrape_rows(csv_path=Path("docs/cruise_prices_rcc.csv"))
    msc = read_latest_scrape_rows(csv_path=Path("docs/cruise_prices_msc.csv"))

    combined_rows = sorted(
        rcc.rows + msc.rows,
        key=lambda r: _parse_price_to_float(r.get("price", "")),
    )

    later_timestamp = (
        rcc.scrape_timestamp_raw
        if rcc.scrape_timestamp_raw > msc.scrape_timestamp_raw
        else msc.scrape_timestamp_raw
    )

    later_date = (
        rcc.scrape_date_ddmmyyyy
        if rcc.scrape_timestamp_raw > msc.scrape_timestamp_raw
        else msc.scrape_date_ddmmyyyy
    )

    html = build_html_email(
        scrape_date_ddmmyyyy=later_date,
        rows=combined_rows,
    )

    subject_date = _format_subject_date(later_timestamp)
    subject = f"Cruise Prices — {subject_date}"
    send_mail_html(
        html=html,
        subject=subject,
        recipients=recipients,
        sender_address=sender_address,
        sender_password=sender_password,
    )


if __name__ == "__main__":
    main()
