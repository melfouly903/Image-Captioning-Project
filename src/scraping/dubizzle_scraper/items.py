"""
items.py
--------
Defines the data model for a single mobile phone listing.
Scrapy uses Item classes to structure scraped data in a consistent,
validated way — similar to a typed dict.
"""

import scrapy


class MobilePhoneItem(scrapy.Item):
    """
    Represents one mobile phone listing scraped from Dubizzle.

    Fields
    ------
    price       : Asking price as a cleaned string, e.g. "EGP 12,500"
    description : Listing title / short description
    image_url   : URL of the primary listing thumbnail
    listing_url : Canonical URL of the individual ad (used for dedup)
    scraped_at  : ISO-8601 timestamp when the item was collected
    """

    price       = scrapy.Field()
    description = scrapy.Field()
    image_url   = scrapy.Field()
    listing_url = scrapy.Field()
    scraped_at  = scrapy.Field()
