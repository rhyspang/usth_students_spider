#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 17-6-24 下午12:31
# @Author  : rhys
# @Software: PyCharm
# @Project : students
import scrapy
from enum import Enum


class StudentBaseSpider(scrapy.Spider):
    def parse(self, response):
        pass

    allowed_domains = ["60.219.165.24"]
    start_urls = ['http://60.219.165.24/']
    domain = 'http://60.219.165.24/'
    login_url = 'loginAction.do'

    LOGIN_STATUS = Enum('LOGIN_STATUS', 'SUCCESS WRONG_ID WRONG_PASS')

    def _check_login_status(self, response):
        flag_tag = response.css('td[class="errorTop"] font::text').extract_first()
        if flag_tag is None:
            return self.LOGIN_STATUS.SUCCESS
        else:
            if flag_tag.find(u'证件号不存在') != -1:
                return self.LOGIN_STATUS.WRONG_ID
            else:
                return self.LOGIN_STATUS.WRONG_PASS
