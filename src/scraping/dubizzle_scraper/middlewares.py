"""
middlewares.py
--------------
Custom Scrapy middlewares:

1. RotatingUserAgentMiddleware  — cycles through a pool of realistic
   browser User-Agent strings so every request looks different.

2. SeleniumMiddleware           — transparent fallback that renders pages
   with a headless Chrome browser when USE_SELENIUM = True in settings.
   Activated only for requests that set meta['use_selenium'] = True, OR
   for every request when settings.USE_SELENIUM is True.

3. ItemCountMiddleware          — spider middleware that watches the
   running item count and raises CloseSpider once TARGET_MAX is reached.
"""

import logging
import random
import time
from typing import Optional

from scrapy import signals
from scrapy.exceptions import CloseSpider, NotConfigured
from scrapy.http import HtmlResponse

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────
# 1. Rotating User-Agent
# ─────────────────────────────────────────────────────────────

# Pool of realistic desktop + mobile User-Agent strings (mid-2024).
USER_AGENTS = [
    # Chrome on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",

    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",

    # Chrome on macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",

    # Firefox on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) "
    "Gecko/20100101 Firefox/125.0",

    # Firefox on Linux
    "Mozilla/5.0 (X11; Linux x86_64; rv:125.0) "
    "Gecko/20100101 Firefox/125.0",

    # Safari on macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4_1) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.4.1 Safari/605.1.15",

    # Edge on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0",

    # Chrome on Android
    "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",

    # Safari on iPhone
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4_1 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 "
    "Mobile/15E148 Safari/604.1",
]


class RotatingUserAgentMiddleware:
    """
    Downloader middleware that sets a random User-Agent on every request.
    Replaces Scrapy's built-in UserAgentMiddleware.
    """

    def process_request(self, request, spider):
        agent = random.choice(USER_AGENTS)
        request.headers["User-Agent"] = agent
        logger.debug("User-Agent → %s", agent[:60])


# ─────────────────────────────────────────────────────────────
# 2. Selenium Middleware
# ─────────────────────────────────────────────────────────────

class SeleniumMiddleware:
    """
    Transparent Selenium fallback for JavaScript-rendered pages.

    Activation
    ----------
    • Set  USE_SELENIUM = True  in settings.py  to enable for ALL requests.
    • Or set  request.meta['use_selenium'] = True  per-request.

    The middleware returns a Scrapy HtmlResponse populated with the fully
    rendered DOM, so all downstream selectors work identically.
    """

    def __init__(self, use_selenium: bool, driver_args: list):
        self.use_selenium = use_selenium
        self.driver_args  = driver_args
        self.driver       = None

    @classmethod
    def from_crawler(cls, crawler):
        use_selenium = crawler.settings.getbool("USE_SELENIUM", False)
        driver_args  = crawler.settings.getlist("SELENIUM_DRIVER_ARGUMENTS", [])

        if not use_selenium:
            # Raise NotConfigured so Scrapy removes this middleware entirely.
            raise NotConfigured("USE_SELENIUM is False — Selenium middleware disabled.")

        mw = cls(use_selenium, driver_args)
        crawler.signals.connect(mw.spider_closed, signal=signals.spider_closed)
        return mw

    def _get_driver(self):
        """Lazy-initialise the Chrome WebDriver on first use."""
        if self.driver is not None:
            return self.driver

        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service

        opts = Options()
        for arg in self.driver_args:
            opts.add_argument(arg)

        # Suppress the "Chrome is being controlled by automated software" bar.
        opts.add_experimental_option("excludeSwitches", ["enable-automation"])
        opts.add_experimental_option("useAutomationExtension", False)

        try:
            # Try webdriver-manager for automatic chromedriver management.
            from webdriver_manager.chrome import ChromeDriverManager
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=opts)
        except Exception:
            # Fall back to system chromedriver on PATH.
            self.driver = webdriver.Chrome(options=opts)

        logger.info("Selenium Chrome WebDriver initialised.")
        return self.driver

    def process_request(self, request, spider):
        """
        Intercept the request, render it with Chrome, and return an
        HtmlResponse containing the fully-rendered HTML.
        """
        use_sel = request.meta.get("use_selenium", self.use_selenium)
        if not use_sel:
            return None   # pass through to normal downloader

        driver = self._get_driver()
        driver.get(request.url)

        # Give JS time to render (a smarter wait would use WebDriverWait).
        time.sleep(3)

        body = driver.page_source.encode("utf-8")
        return HtmlResponse(
            url=driver.current_url,
            body=body,
            encoding="utf-8",
            request=request,
        )

    def spider_closed(self):
        """Quit the browser when the spider finishes."""
        if self.driver:
            self.driver.quit()
            logger.info("Selenium WebDriver closed.")


# ─────────────────────────────────────────────────────────────
# 3. Item-Count Spider Middleware (auto-stop)
# ─────────────────────────────────────────────────────────────

class ItemCountMiddleware:
    """
    Spider middleware that monitors how many valid items have been
    yielded and raises CloseSpider once TARGET_MAX is reached.

    NOTE: The actual counter lives in the pipeline (CsvExportPipeline)
    which is the single source of truth for *valid* items. This middleware
    reads that counter via spider.crawler.stats.
    """

    def __init__(self, target_max: int):
        self.target_max = target_max

    @classmethod
    def from_crawler(cls, crawler):
        return cls(target_max=crawler.settings.getint("TARGET_MAX", 6_000))

    def process_spider_output(self, response, result, spider):
        """
        Pass items/requests through; after each batch check the
        item count and close the spider if we've hit the target.
        """
        for item_or_request in result:
            yield item_or_request

        valid_count = spider.crawler.stats.get_value("valid_items", 0)
        if valid_count >= self.target_max:
            logger.info(
                "TARGET_MAX reached (%d items). Closing spider.", valid_count
            )
            raise CloseSpider(f"Collected {valid_count} valid items (target: {self.target_max})")
