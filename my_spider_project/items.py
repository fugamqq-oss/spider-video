import scrapy


class VideoCandidateItem(scrapy.Item):
    url = scrapy.Field()
    platform = scrapy.Field()
    title = scrapy.Field()
    summary = scrapy.Field()
    publishedAt = scrapy.Field()
    buzzScore = scrapy.Field()
    saturationLevel = scrapy.Field()
    rationale = scrapy.Field()
    sourcePage = scrapy.Field()
    topic = scrapy.Field()
