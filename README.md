# Cruise Scanner 🚢

Automated Royal Caribbean cruise price tracker with analytics and deal notifications.

## Pages
https://fergalmoylan.github.io/cruise-scanner/app/

## Features

- 🔍 Daily automated scraping of Royal Caribbean cruise prices
- 📊 Price history tracking and trend analysis
- 📧 Email notifications for price drops and deals
- 📈 Web dashboard with interactive charts
- 🔄 Resilient to website changes with multi-strategy parsing
- 💰 Completely free using GitHub Actions and GitHub Pages

## Quick Start

### Prerequisites

- Python 3.9+
- Git
- GitHub account

### Local Development Setup

1. Clone the repository:
```bash
git clone https://github.com/YOUR_USERNAME/cruise-price-tracker.git
cd cruise-price-tracker
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

src
├── __init__.py
├── analytics             # Price analysis and trends
├── main.py               # entrypoint script
├── notifications         # notifications (alerts / emails)
└── scraper               # Web scraping logic
data
├── cruise_prices_v2.csv  # csv with all scraped data
├── processed             # json formatted scraped data
└── raw                   # raw json scraped data
.github
└── workflows             # GitHub Actions automation
```

## Configuration

### GitHub Actions Setup

1. Go to your repository Settings → Secrets and variables → Actions
2. Add the following secrets:
   - `EMAIL_USERNAME`: Your Gmail address
   - `EMAIL_PASSWORD`: Gmail app-specific password
   - `EMAIL_RECIPIENT`: Where to send notifications

### Email Notifications

1. Enable 2-factor authentication on Gmail
2. Generate an app-specific password:
   - Go to Google Account settings
   - Security → 2-Step Verification → App passwords
   - Generate a password for "Mail"
3. Use this password in GitHub Secrets

## Usage

### Manual Scraping
```bash
python src/main.py --scrape
```

### View Dashboard
The dashboard is automatically deployed to:
`https://YOUR_USERNAME.github.io/cruise-price-tracker/`

## Development

### Running Tests
```bash
pytest tests/
```

### Updating Selectors
Edit `config/selectors.json` if the website structure changes.

## License

MIT

## Contributing

Pull requests are welcome! Please read CONTRIBUTING.md first.

## Disclaimer

This tool is for personal use only. Please respect Royal Caribbean's terms of service and implement appropriate rate limiting.
