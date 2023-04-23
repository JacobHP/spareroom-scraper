import datetime
import logging
from typing import Iterator, Any
import scrapy
from scrapy.loader import ItemLoader
from items import Listing


logging.getLogger('scrapy.core.scraper').addFilter(
    lambda x: not x.getMessage().startswith('Scraped from')
)


class SpareroomSpider(scrapy.Spider):
    """Spareroom Scrapy Spider"""

    name = 'spareroom'
    custom_settings = {
        'AUTOTHROTTLE_ENABLED': False,
        'FEED_URI': 'data/%(name)s/{date}/%(location)s_%(time)s.json'.format(date=datetime.date.today()),
        'FEED_FORMAT': 'json'
    }

    def __init__(self, location):
        super().__init__()
        self.location = location
        self.start_urls = [f"https://www.spareroom.co.uk/flatshare/{location}&sort_by=last_updated/page{i}" for i in range(1, 101)]

    def parse(
            self, 
            response: scrapy.http.Response
        ) -> Iterator[scrapy.http.Request]:
        """
        Parse a spareroom page for a list of property listings
        and yield individual parsed listings
        """
        l = ItemLoader(item=Listing(), response=response)
        for href in response.xpath("//figure/a/@href").getall():
            url = f'https://www.spareroom.co.uk{href}'
            try:
                yield scrapy.Request(url, callback=self.parse_listing)
            except ValueError as ex:
                if str(ex) == '''Port could not be cast to integer value as "alert('Sorry, this room is no longer available');"''':
                    continue
                raise ex
    
    def parse_listing(
            self, 
            response: scrapy.http.Response
            ) -> Any:
        """Parse a spareroom room listing"""

        l = ItemLoader(item=Listing(), response=response)
        l.add_xpath('ad_ref',
                    "//p[@id='listing_ref']//text()")
        l.add_xpath('listing_type', 
                    "//ul[@class='key-features']//li[@class='key-features__feature']//text()")
        l.add_xpath('room_price', 
                    "//section[starts-with(@class, 'feature feature--price')]//li[@class='room-list__room']//text()")
        l.add_xpath('property_price', 
                    "//section[starts-with(@class, 'feature feature--price-whole-property')]//text()")
        l.add_xpath('room_available', 
                    "//section[@class='feature feature--availability']//dl[@class='feature-list']//text()")
        l.add_xpath('room_deposit', 
                    "//section[@class='feature feature--extra-cost']//dl[@class='feature-list']//text()")
        l.add_xpath('amenities', 
                    "//section[@class='feature feature--amenities']//dl[@class='feature-list']//text()")
        l.add_xpath('current_household', 
                    "//section[@class='feature feature--current-household']//dl[@class='feature-list']//text()")
        l.add_xpath('household_preferences', 
                    "//section[@class='feature feature--household-preferences']//dl[@class='feature-list']//text()")
        return l.load_item()