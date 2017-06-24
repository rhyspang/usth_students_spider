# -*- coding: utf-8 -*-

import pymysql
import scrapy
from students.items import Curriculum
from students.spiders.student_base_spider import StudentBaseSpider


class SemesterGradeSpider(StudentBaseSpider):
    name = "semester_grade"
    semester_grade_url = 'bxqcjcxAction.do'
    all_grade_url = 'gradeLnAllAction.do?type=ln&oper=fainfo'

    def start_requests(self):
        for sid, password in self.get_sids_passwords():
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
        if login_status == self.LOGIN_STATUS.WRONG_PASS:
            self.logger.error("user[{}] has invalid password[{}]"
                              .format(response.meta['sid'], response.meta['password']))
            return
        else:
            yield scrapy.Request(self.domain + self.all_grade_url,
                                 callback=self.parse_grades,
                                 dont_filter=True,
                                 meta={'sid': response.meta['sid'],
                                       'password': response.meta['password'],
                                       'flag': 'all',
                                       'cookiejar': response.meta['cookiejar']})

    @staticmethod
    def parse_grades(response):
        def extract_with_xpath(root, query):
            return root.xpath(query).extract_first().strip()

        all_grades = response.xpath('//table[@id="user"]/tr')
        counts = len(all_grades)
        for grade in all_grades:
            curriculum = Curriculum()
            curriculum['cid'] = extract_with_xpath(grade, 'td[1]/text()')
            curriculum['name'] = extract_with_xpath(grade, 'td[3]/text()')
            curriculum['credit'] = extract_with_xpath(grade, 'td[5]/text()')
            curriculum['is_compulsory'] = 1 if extract_with_xpath(grade, 'td[6]/text()') == u'必修' else 0
            curriculum['score'] = extract_with_xpath(grade, 'td[7]/p/text()')
            curriculum['sid'] = response.meta['sid']
            curriculum['all'] = counts
            yield curriculum

    def get_sids_passwords(self):
        sql = "SELECT sid, password FROM `students_all` " \
              "WHERE password IS NOT NULL AND book_email=1;"
        conn = pymysql.connect(**self.settings.get('MYSQL_DB_KWARGS'))
        try:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                result = cursor.fetchone()
                while result:
                    yield result
                    result = cursor.fetchone()
        finally:
            conn.close()
