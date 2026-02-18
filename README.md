# Cruise Scanner

Automated Royal Caribbean cruise price tracker with analytics and deal notifications.

*This is a personal project and a work in progress.*

## Pages
https://fergalmoylan.github.io/cruise-scanner/app/

## Quick Start

### Prerequisites

- Python 3.9+
- Git
- GitHub account

### Local Development Setup

1. Clone the repository:
```bash
git clone https://github.com/YOUR_USERNAME/cruise-scanner.git
cd cruise-scanner
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
playwright install
```

4. Copy environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Run the scraper manually:
```bash
python src/main.py --scrape
```

## Project Structure

```
├── data
│   ├── processed               # json formatted scraped data
│   └── raw                     # raw json scraped data
├── docs
│   ├── app                     # Github pages assets and resources
│   └── cruise_prices_v2.csv    # Cruise data CSV file written by TS app
├── src
│   ├── __init__.py
│   ├── analytics               # Price analysis and trends
│   ├── main.py                 # entrypoint script
│   ├── notifications           # notifications (alerts / emails)
│   └── scraper                 # Web scraping logic
├── tests
│   └── test_scraper.py
├── web                         # Typescript UI Application
└── .github
    └── workflows               # GitHub Actions automation
```

### Manual Scraping
```bash
python src/main.py --scrape
```

### View Pages
The UI is automatically deployed to:
`https://YOUR_USERNAME.github.io/cruise-scanner/`

### Running Tests
```bash
pytest tests/
```

### Updating Selectors
Edit `config/selectors.json` if the website structure changes.

## License

MIT

## Disclaimer

This tool is for personal use only. Please respect Royal Caribbean's terms of service and implement appropriate rate limiting.
