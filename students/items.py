# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class StudentItem(scrapy.Item):
    sid = scrapy.Field()
    name = scrapy.Field()
    id = scrapy.Field()
    gender = scrapy.Field()
    college = scrapy.Field()
    class_name = scrapy.Field()
    nationality = scrapy.Field()
    tel = scrapy.Field()
    email = scrapy.Field()
    avatar = scrapy.Field()