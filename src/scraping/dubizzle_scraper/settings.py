"""
settings.py
-----------
Central configuration for the Dubizzle mobile-phones scraper.
All tuneable knobs live here so nothing is hard-coded in the spider.
"""

# ──────────────────────────────────────────────
# Project identity
# ──────────────────────────────────────────────
BOT_NAME    = "dubizzle_scraper"
SPIDER_MODULES         = ["dubizzle_scraper.spiders"]
NEWSPIDER_MODULE       = "dubizzle_scraper.spiders"


# ──────────────────────────────────────────────
# Scraping targets
# ──────────────────────────────────────────────
# Stop automatically once we hit TARGET_MAX valid listings.
TARGET_MIN = 4_000   # minimum acceptable dataset size
TARGET_MAX = 6_000   # hard stop (spider closes itself)

# Save a checkpoint CSV every N valid items (crash-safety).
CHECKPOINT_EVERY = 500


# ──────────────────────────────────────────────
# Politeness / anti-ban settings
# ──────────────────────────────────────────────
# Random delay between (0.5 * DOWNLOAD_DELAY) and (1.5 * DOWNLOAD_DELAY)
DOWNLOAD_DELAY           = 1.5      # seconds
RANDOMIZE_DOWNLOAD_DELAY = True

# Limit concurrent requests so we don't hammer the server.
CONCURRENT_REQUESTS             = 4
CONCURRENT_REQUESTS_PER_DOMAIN  = 4

# Respect robots.txt — set False only if the site's robots.txt blocks
# the category page (check manually before changing).
ROBOTSTXT_OBEY = False

# Follow redirects automatically.
REDIRECT_ENABLED = True
REDIRECT_MAX_TIMES = 5


# ──────────────────────────────────────────────
# Retry configuration (built-in Scrapy middleware)
# ──────────────────────────────────────────────
RETRY_ENABLED    = True
RETRY_TIMES      = 3          # retry up to 3 times on failure
RETRY_HTTP_CODES = [429, 500, 502, 503, 504, 522, 524, 408]


# ──────────────────────────────────────────────
# Default HTTP headers
# ──────────────────────────────────────────────
DEFAULT_REQUEST_HEADERS = {
    "Accept"         : "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection"     : "keep-alive",
    "Cache-Control"  : "no-cache",
}


# ──────────────────────────────────────────────
# Middleware stack
# ──────────────────────────────────────────────
DOWNLOADER_MIDDLEWARES = {
    # Disable Scrapy's default UserAgent middleware …
    "scrapy.downloadermiddlewares.useragent.UserAgentMiddleware": None,
    # … and replace it with our rotating one.
    "dubizzle_scraper.middlewares.RotatingUserAgentMiddleware": 400,

    # Selenium fallback — only activated when USE_SELENIUM = True.
    "dubizzle_scraper.middlewares.SeleniumMiddleware": 800,

    # Built-in retry (keep enabled).
    "scrapy.downloadermiddlewares.retry.RetryMiddleware": 550,
}

SPIDER_MIDDLEWARES = {
    # Custom middleware that signals the spider to stop at TARGET_MAX.
    "dubizzle_scraper.middlewares.ItemCountMiddleware": 100,
}


# ──────────────────────────────────────────────
# Pipeline stack
# ──────────────────────────────────────────────
ITEM_PIPELINES = {
    # 1. Validate & clean (drop incomplete / bad items)
    "dubizzle_scraper.pipelines.CleaningPipeline"    : 100,
    # 2. Deduplicate by listing URL
    "dubizzle_scraper.pipelines.DeduplicationPipeline": 200,
    # 3. Export to CSV (with periodic checkpoints)
    "dubizzle_scraper.pipelines.CsvExportPipeline"   : 300,
}


# ──────────────────────────────────────────────
# Output / logging
# ──────────────────────────────────────────────
LOG_LEVEL = "INFO"
LOG_FILE  = "scraper.log"

# Feed exports are handled by our custom pipeline instead, but keep
# the built-in feed disabled to avoid duplicate output.
FEEDS = {}


# ──────────────────────────────────────────────
# Selenium toggle (set True if JS rendering needed)
# ──────────────────────────────────────────────
USE_SELENIUM = True   

# Path to chromedriver (leave empty to use webdriver-manager auto-detection)
SELENIUM_DRIVER_NAME       = "chrome"
SELENIUM_DRIVER_EXECUTABLE_PATH = None   # None → auto-detect via webdriver-manager
SELENIUM_BROWSER_EXECUTABLE_PATH = None
SELENIUM_COMMAND_EXECUTOR  = None

# Chrome options passed to Selenium (headless by default)
SELENIUM_DRIVER_ARGUMENTS  = [
    "--headless=new",
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-blink-features=AutomationControlled",
    "--window-size=1920,1080",
]


# ──────────────────────────────────────────────
# Cookies & telemetry
# ──────────────────────────────────────────────
COOKIES_ENABLED = True
TELEMETRY_ENABLED = False
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
