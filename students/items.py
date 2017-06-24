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
    password = scrapy.Field()
    book_email = scrapy.Field()


class Curriculum(scrapy.Item):
    cid = scrapy.Field()
    sid = scrapy.Field()
    name = scrapy.Field()
    credit = scrapy.Field()
    is_compulsory = scrapy.Field()
    score = scrapy.Field()
    term = scrapy.Field()
    is_new = scrapy.Field()
    all = scrapy.Field()
