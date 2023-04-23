BOT_NAME = "spareroom-scraper"

SPIDER_MODULES = ["spiders"]
NEWSPIDER_MODULE = "spiders"

USER_AGENT = "spareroom-scraper"
ROBOTSTXT_OBEY = True
FEEDS = { f"data/%(name)s/items_{'derby'}.json": {"format": "json"},}
CONCURRENT_REQUESTS = 16

DOWNLOAD_DELAY = 0.1
#CONCURRENT_REQUESTS_PER_DOMAIN = 16
#CONCURRENT_REQUESTS_PER_IP = 16

COOKIES_ENABLED = False

#DEFAULT_REQUEST_HEADERS = {
#    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
#    "Accept-Language": "en",
#}


ITEM_PIPELINES = {
   "pipelines.SpareRoomPipeline": 300,
}

AUTOTHROTTLE_ENABLED = False
#AUTOTHROTTLE_START_DELAY = 5
#AUTOTHROTTLE_MAX_DELAY = 60
#AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
#AUTOTHROTTLE_DEBUG = False

REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"
