"""
pipelines.py
------------
Three-stage pipeline:

Stage 1 — CleaningPipeline
    • Strips leading/trailing whitespace from all string fields.
    • Normalises internal whitespace (multiple spaces → one space).
    • Drops items that are missing price, description, or image_url.

Stage 2 — DeduplicationPipeline
    • Keeps a set of seen listing_url values.
    • Drops any item whose URL was already seen (exact duplicate ad).

Stage 3 — CsvExportPipeline
    • Accumulates valid items in memory.
    • Saves a checkpoint CSV every CHECKPOINT_EVERY items.
    • Writes the final mobile_phones.csv when the spider closes.
    • Prints a summary to stdout at the end.
"""

import csv
import logging
import os
import re
from datetime import datetime, timezone
from typing import Set

import pandas as pd

from dubizzle_scraper.items import MobilePhoneItem

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────

def clean_text(value: str) -> str:
    """
    Remove leading/trailing whitespace and collapse internal
    whitespace sequences (spaces, tabs, newlines) to a single space.
    """
    if not isinstance(value, str):
        return value
    return re.sub(r"\s+", " ", value).strip()


def is_valid_url(url: str) -> bool:
    """Basic check that a URL looks like a real HTTP(S) URL."""
    return isinstance(url, str) and url.startswith(("http://", "https://"))


# ─────────────────────────────────────────────────────────────
# Stage 1: Cleaning & Validation
# ─────────────────────────────────────────────────────────────

class CleaningPipeline:
    """
    Cleans all text fields and drops items with any required field missing.
    Required fields: price, description, image_url.
    """

    REQUIRED_FIELDS = ("price", "description", "image_url")

    def process_item(self, item: MobilePhoneItem, spider):
        # ── Clean text fields ──────────────────────────────────
        for field in ("price", "description"):
            if field in item:
                item[field] = clean_text(item[field])

        # ── Validate required fields ───────────────────────────
        for field in self.REQUIRED_FIELDS:
            value = item.get(field)
            if not value:
                # Drop the item — missing a required field.
                logger.debug("Dropping item (missing %s): %s", field, item.get("listing_url"))
                spider.crawler.stats.inc_value("dropped/missing_field")
                raise DropItem(f"Missing required field: {field}")

        # Extra check: image_url must look like a real URL.
        if not is_valid_url(item.get("image_url", "")):
            logger.debug("Dropping item (invalid image_url): %s", item.get("image_url"))
            spider.crawler.stats.inc_value("dropped/invalid_image_url")
            raise DropItem(f"Invalid image_url: {item.get('image_url')}")

        # Stamp the scrape time if the spider didn't set it.
        if not item.get("scraped_at"):
            item["scraped_at"] = datetime.now(timezone.utc).isoformat()

        return item


# ─────────────────────────────────────────────────────────────
# Stage 2: Deduplication
# ─────────────────────────────────────────────────────────────

class DeduplicationPipeline:
    """
    Drops items whose listing_url has already been seen.
    Uses an in-memory set — fast O(1) lookups.
    """

    def __init__(self):
        self.seen_urls: Set[str] = set()

    def process_item(self, item: MobilePhoneItem, spider):
        url = item.get("listing_url", "")
        if url in self.seen_urls:
            logger.debug("Duplicate skipped: %s", url)
            spider.crawler.stats.inc_value("dropped/duplicate")
            raise DropItem(f"Duplicate listing: {url}")

        self.seen_urls.add(url)
        return item


# ─────────────────────────────────────────────────────────────
# Stage 3: CSV Export with Checkpoints
# ─────────────────────────────────────────────────────────────

class CsvExportPipeline:
    """
    Accumulates valid items and writes them to CSV.

    • Saves a checkpoint file every CHECKPOINT_EVERY items so that a
      crash doesn't lose all progress.
    • Writes the final mobile_phones.csv on spider_close.
    • Increments the 'valid_items' Scrapy stat so ItemCountMiddleware
      can decide when to stop the spider.
    """

    OUTPUT_FILE      = "mobile_phones.csv"
    CHECKPOINT_FILE  = "mobile_phones_checkpoint.csv"

    FIELDNAMES = ["price", "description", "image_url", "listing_url", "scraped_at"]

    def __init__(self, checkpoint_every: int, target_min: int, target_max: int):
        self.checkpoint_every = checkpoint_every
        self.target_min       = target_min
        self.target_max       = target_max
        self.items            = []          # in-memory buffer
        self.count            = 0           # valid items so far

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            checkpoint_every = crawler.settings.getint("CHECKPOINT_EVERY", 500),
            target_min       = crawler.settings.getint("TARGET_MIN", 4_000),
            target_max       = crawler.settings.getint("TARGET_MAX", 6_000),
        )

    # ── Incremental write setup ────────────────────────────────

    def open_spider(self, spider):
        """
        Open the output CSV and write the header row immediately,
        so partial runs always produce a valid CSV.
        """
        self._csv_file = open(self.OUTPUT_FILE, "w", newline="", encoding="utf-8")
        self._writer   = csv.DictWriter(self._csv_file, fieldnames=self.FIELDNAMES)
        self._writer.writeheader()
        logger.info("CSV output opened: %s", self.OUTPUT_FILE)

    # ── Item processing ────────────────────────────────────────

    def process_item(self, item: MobilePhoneItem, spider):
        row = {f: item.get(f, "") for f in self.FIELDNAMES}
        self._writer.writerow(row)
        self._csv_file.flush()   # ensure it's on disk

        self.items.append(dict(row))
        self.count += 1

        # Update the global valid_items stat (read by ItemCountMiddleware).
        spider.crawler.stats.set_value("valid_items", self.count)

        # Progress log every 100 items.
        if self.count % 100 == 0:
            logger.info("✔  %d valid items collected so far …", self.count)

        # Periodic checkpoint save.
        if self.count % self.checkpoint_every == 0:
            self._save_checkpoint()

        return item

    # ── Finalise ───────────────────────────────────────────────

    def close_spider(self, spider):
        """Flush, close the incremental file, then write the tidy final CSV."""
        self._csv_file.flush()
        self._csv_file.close()

        # Re-save as a proper pandas DataFrame for quality.
        self._save_final()

        # Print summary.
        print("\n" + "=" * 55)
        print(f"  Scraping complete!")
        print(f"  Total valid items collected : {self.count:,}")
        print(f"  Output file                 : {self.OUTPUT_FILE}")
        if self.count < self.target_min:
            print(f"  ⚠  Below minimum target ({self.target_min:,}). "
                  "Consider re-running or checking selectors.")
        print("=" * 55 + "\n")

    # ── Internal helpers ───────────────────────────────────────

    def _save_checkpoint(self):
        """Save current buffer to checkpoint file (CSV)."""
        if not self.items:
            return
        df = pd.DataFrame(self.items)
        df.to_csv(self.CHECKPOINT_FILE, index=False, encoding="utf-8")
        logger.info("Checkpoint saved: %d items → %s", self.count, self.CHECKPOINT_FILE)

    def _save_final(self):
        """
        Load the incremental CSV with pandas, deduplicate one more time
        (safety net), sort by listing_url, and overwrite the output file.
        """
        if not self.items:
            logger.warning("No items to save.")
            return

        df = pd.DataFrame(self.items)

        # Final dedup pass (belt-and-suspenders).
        before = len(df)
        df = df.drop_duplicates(subset=["listing_url"])
        dupes_removed = before - len(df)
        if dupes_removed:
            logger.info("Final dedup removed %d duplicate rows.", dupes_removed)

        # Sort for reproducibility.
        df.sort_values("listing_url", inplace=True, ignore_index=True)

        df.to_csv(self.OUTPUT_FILE, index=False, encoding="utf-8")
        logger.info("Final CSV saved: %d rows → %s", len(df), self.OUTPUT_FILE)


# ─────────────────────────────────────────────────────────────
# We need to import DropItem *after* the class definitions so
# the exception is available to the pipeline methods above.
# ─────────────────────────────────────────────────────────────
from scrapy.exceptions import DropItem  # noqa: E402 (placed here intentionally)
