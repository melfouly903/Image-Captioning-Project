"""
mobiles_spider.py
-----------------
Scrapy spider that crawls the Dubizzle Egypt mobile-phones category
and extracts price, description, and image URL for each listing.

Architecture
------------
• Starts at the category landing page.
• Parses all listing cards on the page.
• Follows the "next page" link and repeats until:
    – there is no next page, OR
    – TARGET_MAX valid items have been collected
      (enforced by ItemCountMiddleware).

Selector Strategy
-----------------
Dubizzle renders its listing grid with predictable class names / data
attributes. The spider uses CSS selectors as the primary strategy and
falls back to XPath where needed.

Because Dubizzle's HTML structure may change over time, every selector
is isolated in the `_selectors` dict so you only need to update one
place when the site changes.

JavaScript Rendering Note
-------------------------
If the listing cards are absent from the raw HTML (i.e. the page is a
React/Next.js SPA that renders client-side), set USE_SELENIUM = True in
settings.py. The SeleniumMiddleware will then render each page with a
headless Chrome browser before passing the response to this spider —
no other code changes are required.
"""

import logging
from datetime import datetime, timezone
from typing import Generator, Optional
from urllib.parse import urljoin, urlencode, urlparse, parse_qs, urlunparse

import scrapy

from dubizzle_scraper.items import MobilePhoneItem

logger = logging.getLogger(__name__)


class MobilesSpider(scrapy.Spider):
    """
    Spider name : mobiles
    Start URL   : https://www.dubizzle.com.eg/en/mobile-phones-tablets-accessories-numbers/mobile-phones/
    """

    name = "mobiles"
    allowed_domains = ["dubizzle.com.eg"]

    # ── Category entry point ─────────────────────────────────
    BASE_URL = (
        "https://www.dubizzle.com.eg/en/"
        "mobile-phones-tablets-accessories-numbers/mobile-phones/"
    )

    # ── CSS / XPath selector map ─────────────────────────────
    # Isolate every selector here so site changes need only one edit.
    _selectors = {
        # ── Listing card (one card = one phone ad) ────────────
        # Dubizzle wraps each listing in an <article> or a <li>
        # with a data attribute. Adjust the selector below to match
        # what you see in DevTools → Elements on the category page.
        "listing_cards": [
            # Primary: article elements inside the listing grid
            "article.b-advert-tile",
            # Alternative 1: li elements
            "li[class*='listing']",
            # Alternative 2: generic article
            "article",
        ],

        # ── Inside each card ──────────────────────────────────
        "title": [
            "div[aria-label='Title']::text",  # ضفنا السطر ده
            "[class*='title']::text",
            "h2::text",
            "h3::text",
            "[data-testid*='title']::text",
        ],
        "price": [
            "span[aria-label='Price']::text",
            "div[aria-label='Price']::text",
            "[data-aut-id='itemPrice']::text",
            "[class*='price']::text",
            "._27875835::text", 
            "strong::text",
        ],
        "image": [
            "img::attr(src)",
            "img::attr(data-src)",
            "img::attr(data-lazy-src)",
            "[class*='image'] img::attr(src)",
        ],
        "link": [
            "a::attr(href)",
            "[class*='link']::attr(href)",
        ],

        # ── Pagination ────────────────────────────────────────
        "next_page": [
            "a[aria-label='Next']::attr(href)",
            "a[data-testid='next-page']::attr(href)",
            "a[class*='next']::attr(href)",
            "a[rel='next']::attr(href)",
            "li.next a::attr(href)",
        ],
    }

    # ────────────────────────────────────────────────────────
    # Lifecycle
    # ────────────────────────────────────────────────────────

    def start_requests(self):
        """
        Yield the initial request for page 1 of the category.
        Extra headers mimic a real browser visiting from Google.
        """
        headers = {
            "Referer"          : "https://www.google.com/",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest"   : "document",
            "Sec-Fetch-Mode"   : "navigate",
            "Sec-Fetch-Site"   : "none",
            "Sec-Fetch-User"   : "?1",
        }
        yield scrapy.Request(
            url=self.BASE_URL,
            headers=headers,
            callback=self.parse,
            errback=self.handle_error,
            meta={
                "page": 1,
                # Set True here (or in settings.py) to use Selenium:
                # "use_selenium": True,
            },
        )

    # ────────────────────────────────────────────────────────
    # Page parser
    # ────────────────────────────────────────────────────────

    def parse(self, response) -> Generator:
        """
        Parse a category listing page.

        1. Extract all listing cards.
        2. Yield one MobilePhoneItem per card (after validation).
        3. Follow the next-page link (if present and within limits).
        """
        page = response.meta.get("page", 1)
        logger.info("Parsing page %d — %s", page, response.url)

        # ── Find listing cards ─────────────────────────────────
        cards = self._find_cards(response)

        if not cards:
            logger.warning(
                "No listing cards found on page %d. "
                "The site may be JS-rendered — try USE_SELENIUM = True.",
                page,
            )
        else:
            logger.info("Found %d listing cards on page %d.", len(cards), page)

        # ── Parse each card ────────────────────────────────────
        for card in cards:
            item = self._parse_card(card, response)
            if item:
                yield item

        # ── Follow pagination ──────────────────────────────────
        next_url = self._get_next_page_url(response)
        if next_url:
            yield scrapy.Request(
                url=next_url,
                callback=self.parse,
                errback=self.handle_error,
                meta={
                    "page": page + 1,
                    "use_selenium": response.meta.get("use_selenium", False),
                },
            )
        else:
            logger.info("No next page found after page %d. Crawl complete.", page)

    # ────────────────────────────────────────────────────────
    # Card parsing helpers
    # ────────────────────────────────────────────────────────

    def _find_cards(self, response) -> list:
        """
        Try each card selector in order and return the first non-empty result.
        This makes the spider resilient to minor HTML structure changes.
        """
        for selector in self._selectors["listing_cards"]:
            cards = response.css(selector)
            if cards:
                logger.debug("Card selector matched: '%s' (%d cards)", selector, len(cards))
                return cards
        return []

    def _parse_card(self, card, response) -> Optional[MobilePhoneItem]:
        """
        Extract price, description, image_url, and listing_url from a
        single listing card. Returns None if extraction fails entirely.
        """
        # ── Description / title ───────────────────────────────
        description = self._extract_first(card, self._selectors["title"])

       
       # ── Price ─────────────────────────────────────────────
        price = self._extract_first(card, self._selectors["price"])
        # السلاح النووي: لو ملقاش السعر بالكلاسات العادية، هيدور على كلمة EGP
        if not price:
            price_match = card.xpath(".//*[contains(text(), 'EGP')]/text()").getall()
            price = " ".join(p.strip() for p in price_match if p.strip()) if price_match else None

        # ── Image URL ─────────────────────────────────────────
        image_url = self._extract_first(card, self._selectors["image"])
        # Some images use relative URLs or data URIs — resolve to absolute.
        if image_url and not image_url.startswith("data:"):
            image_url = urljoin(response.url, image_url)

        # ── Listing URL ───────────────────────────────────────
        href = self._extract_first(card, self._selectors["link"])
        listing_url = urljoin(response.url, href) if href else response.url

        # ── Build item ────────────────────────────────────────
        # Validation happens in CleaningPipeline; we pass raw values here.
        item = MobilePhoneItem(
            price       = price,
            description = description,
            image_url   = image_url,
            listing_url = listing_url,
            scraped_at  = datetime.now(timezone.utc).isoformat(),
        )
        return item

    @staticmethod
    def _extract_first(selector, css_list: list) -> Optional[str]:
        """
        Try each CSS selector in css_list and return the first
        non-empty text value found. Returns None if all fail.
        """
        for css in css_list:
            values = selector.css(css).getall()
            # Flatten and join multiple text nodes, then strip.
            text = " ".join(v.strip() for v in values if v.strip())
            if text:
                return text
        return None

    # ────────────────────────────────────────────────────────
    # Pagination helper
    # ────────────────────────────────────────────────────────

    def _get_next_page_url(self, response) -> Optional[str]:
        """
        Try all next-page selectors and return the absolute URL, or None.

        Also handles Dubizzle's query-string based pagination
        (e.g. ?page=2) as a fallback when there is no explicit <a rel="next">.
        """
        # ── Strategy 1: explicit next link ────────────────────
        for css in self._selectors["next_page"]:
            href = response.css(css).get()
            if href:
                url = urljoin(response.url, href)
                logger.debug("Next page (selector): %s", url)
                return url

        # ── Strategy 2: look for any link containing 'page=' ──
        # e.g. <a href="/en/.../mobile-phones/?page=3">
        for href in response.css("a::attr(href)").getall():
            if "page=" in href:
                full = urljoin(response.url, href)
                # Make sure it's the *next* page (current + 1).
                parsed   = urlparse(full)
                qs       = parse_qs(parsed.query)
                page_val = qs.get("page", ["1"])[0]
                try:
                    if int(page_val) == response.meta.get("page", 1) + 1:
                        logger.debug("Next page (query-string fallback): %s", full)
                        return full
                except ValueError:
                    pass

        # ── Strategy 3: increment ?page= ourselves ────────────
        # Only if we found at least one card (avoids infinite loops on
        # pages that silently return empty results).
        current_page = response.meta.get("page", 1)
        cards_found  = bool(self._find_cards(response))

        if cards_found:
            parsed = urlparse(response.url)
            qs     = parse_qs(parsed.query)
            qs["page"] = [str(current_page + 1)]
            new_query = urlencode({k: v[0] for k, v in qs.items()})
            next_url  = urlunparse(parsed._replace(query=new_query))
            logger.debug("Next page (auto-increment): %s", next_url)
            return next_url

        return None

    # ────────────────────────────────────────────────────────
    # Error handling
    # ────────────────────────────────────────────────────────

    def handle_error(self, failure):
        """Log request failures (timeouts, HTTP errors, etc.)."""
        logger.error(
            "Request failed: %s — %s",
            failure.request.url,
            repr(failure.value),
        )
