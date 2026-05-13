# Dubizzle Mobile Phones Scraper

A production-grade Scrapy project to scrape 4,000–6,000 mobile phone listings from dubizzle.com.eg.

## Project Structure

```
dubizzle_scraper/
├── README.md
├── requirements.txt
├── run_scraper.py          ← Entry point: run this script
├── scrapy.cfg
└── dubizzle_scraper/
    ├── __init__.py
    ├── items.py            ← Data model
    ├── middlewares.py      ← User-Agent rotation, Selenium fallback
    ├── pipelines.py        ← Dedup, cleaning, CSV export
    ├── settings.py         ← All Scrapy configuration
    └── spiders/
        ├── __init__.py
        └── mobiles_spider.py  ← Main spider
```

## Installation

```bash
pip install -r requirements.txt
```

> **Selenium note:** If the site is JavaScript-rendered, also install ChromeDriver:
> ```bash
> # macOS
> brew install chromedriver
> # Ubuntu/Debian
> sudo apt-get install chromium-driver
> # Or via pip
> pip install webdriver-manager
> ```

## Usage

### Simple run (recommended)
```bash
python run_scraper.py
```

### Direct Scrapy CLI
```bash
cd dubizzle_scraper
scrapy crawl mobiles
```

## Output

- **`mobile_phones.csv`** — Final dataset (price, description, image_url, listing_url, scraped_at)
- **`mobile_phones_checkpoint.csv`** — Saved every 500 items (resume safety)
- **`scraper.log`** — Full log file

## Configuration

Edit `dubizzle_scraper/settings.py` to tweak:
| Setting | Default | Description |
|---|---|---|
| `TARGET_MIN` | 4000 | Minimum records to collect |
| `TARGET_MAX` | 6000 | Stop after this many records |
| `DOWNLOAD_DELAY` | 1.5 | Seconds between requests |
| `CHECKPOINT_EVERY` | 500 | Save intermediate CSV every N items |
| `USE_SELENIUM` | False | Enable if JS rendering is needed |

## How It Works

1. **Spider** starts at the category URL and follows pagination links
2. **Middleware** rotates User-Agent headers to avoid blocks
3. **Pipeline** cleans text, deduplicates by URL, and drops incomplete listings
4. **Auto-stop** triggers once `TARGET_MAX` valid items are collected
5. **Checkpoint** saves a CSV every 500 items as a safety net
