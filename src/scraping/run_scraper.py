"""
run_scraper.py
--------------
Convenient entry point to run the Dubizzle mobile-phones spider
from any working directory without needing to `cd` into the project.

Usage
-----
    python run_scraper.py

Optional overrides (environment variables)
------------------------------------------
    TARGET_MAX=5000 python run_scraper.py
    USE_SELENIUM=1  python run_scraper.py
"""

import os
import sys
import logging
from pathlib import Path

# ── Make sure the project root is on sys.path ─────────────────────
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# ── Point Scrapy at our settings module ───────────────────────────
os.environ.setdefault(
    "SCRAPY_SETTINGS_MODULE", "dubizzle_scraper.settings"
)

# ── Allow env-var overrides for common settings ───────────────────
from scrapy.utils.project import get_project_settings

settings = get_project_settings()

if os.environ.get("TARGET_MAX"):
    settings.set("TARGET_MAX", int(os.environ["TARGET_MAX"]))

if os.environ.get("TARGET_MIN"):
    settings.set("TARGET_MIN", int(os.environ["TARGET_MIN"]))

if os.environ.get("USE_SELENIUM", "").strip() in ("1", "true", "yes"):
    settings.set("USE_SELENIUM", True)

if os.environ.get("DOWNLOAD_DELAY"):
    settings.set("DOWNLOAD_DELAY", float(os.environ["DOWNLOAD_DELAY"]))

# ── Configure a console logger so progress is visible ─────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)

# ── Run the spider ─────────────────────────────────────────────────
from scrapy.crawler import CrawlerProcess

def main():
    print("=" * 55)
    print("  Dubizzle Mobile Phones Scraper")
    print(f"  Target: {settings.getint('TARGET_MIN'):,} – {settings.getint('TARGET_MAX'):,} items")
    print(f"  Selenium: {'enabled' if settings.getbool('USE_SELENIUM') else 'disabled'}")
    print(f"  Download delay: {settings.getfloat('DOWNLOAD_DELAY')}s (randomised)")
    print("=" * 55)

    process = CrawlerProcess(settings)
    process.crawl("mobiles")
    process.start()   # blocks until the spider finishes


if __name__ == "__main__":
    main()
