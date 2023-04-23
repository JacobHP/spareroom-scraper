import scrapy


class Listing(scrapy.Item):
    """Item for a spareroom listing"""
    ad_ref = scrapy.Field()
    listing_type = scrapy.Field()
    room_price = scrapy.Field()
    property_price = scrapy.Field()
    room_available = scrapy.Field()
    room_deposit = scrapy.Field()
    amenities = scrapy.Field()
    current_household = scrapy.Field()
    household_preferences = scrapy.Field()
    