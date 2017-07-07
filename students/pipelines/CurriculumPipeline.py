#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 17-7-7 下午6:33
# @Author  : rhys
# @Software: PyCharm
# @Project : students
import math
import pymysql
from scrapy.signalmanager import SignalManager

from students import signals
from students.items import Curriculum
from students.mail.semail import send_message


class CurriculumPipeline(object):
    sql_insert = "INSERT INTO `curriculum_all` " \
                 "(`cid`, `sid`, `name`, " \
                 "`credit`, `is_compulsory`, `score`, `is_new`, `update_date`) " \
                 "VALUES (%s, %s, %s, %s, %s, %s, %s, now())"
    sql_update = "UPDATE `curriculum_all` SET `score`=%s, `update_date`=now() WHERE cid=%s AND sid=%s"
    sql_select = "SELECT score FROM `curriculum_all` WHERE cid=%s AND sid=%s"

    def __init__(self, db_config):
        # 维护新查询到的课程, key:sid(学生学号) value:curriculum list(课程列表)
        self.new_curriculum = {}
        # 维护新查询到的课程的数量, key:sid(学生学号) value:已经检索到的curriculum数量
        self.new_curriculum_count = {}
        # 维护需要更新的课程, key:sid(学生学号) value:curriculum list(课程列表)
        self.update_curriculum = {}
        self.connection = None
        self.db_config = db_config

    @classmethod
    def from_crawler(cls, crawler):
        instance = cls(db_config=crawler.settings.get('MYSQL_DB_KWARGS'))
        sm = SignalManager()
        sm.connect(instance.add_to_db_and_pop, signal=signals.email_sent_ok)
        return instance

    def open_spider(self, spider):
        self.connection = pymysql.connect(**self.db_config)

    def close_spider(self, spider):
        # self.connection.close()
        pass

    def process_item(self, item, spider):
        self.save_curriculum(item, spider)

        return item

    def save_curriculum(self, item, spider):
        if not isinstance(item, Curriculum):
            return

        with self.connection.cursor() as cursor:
            cursor.execute(self.sql_select, (item['cid'], item['sid']))
            score = cursor.fetchone()
            has_record = True if score else False

        if not self.new_curriculum_count.get(item['sid']):
            self.new_curriculum_count[item['sid']] = 1
        else:
            self.new_curriculum_count[item['sid']] += 1

        # 初始化为sid对应value为空列表
        if not self.update_curriculum.get(item['sid']):
            self.update_curriculum[item['sid']] = []
        if not self.new_curriculum.get(item['sid']):
            self.new_curriculum[item['sid']] = []

        # 当数据表中有该条成绩的记录
        if has_record:
            score_is_float = True
            try:
                float(score[0])
            except ValueError:
                score_is_float = False
            # 如果分数类型为浮点型
            if score_is_float:
                if math.fabs(float(score[0]) - float(item['score'])) > 1e-5:
                    self.update_curriculum[item['sid']].append(item)
            # 如果分数为字符类型
            else:
                if score[0] != item['score']:
                    self.update_curriculum[item['sid']].append(item)
                    # cursor.execute(sql_update, (item['score'], item['cid'], item['sid']))
        # 数据表中没有查询到的记录
        else:
            self.new_curriculum[item['sid']].append(item)
            # cursor.execute(sql_insert, (item['cid'], item['sid'], item['name'],
            #                             item['credit'], item['is_compulsory'], item['score'], 1))

        # 当成绩页面上的成绩条目都检索完时,
        if self.new_curriculum_count[item['sid']] == int(item['all']):
            if self.new_curriculum.get(item['sid']) or self.update_curriculum.get(item['sid']):
                name, email = self.get_email_by_sid(item['sid'], self.connection)
                if email.strip():
                    send_message(email,
                                 self.new_curriculum[item['sid']],
                                 self.update_curriculum[item['sid']],
                                 name,
                                 spider,
                                 item['sid'])
                    spider.logger.debug("item['sid']" + 'send email to: ' + email)
                else:
                    spider.logger.debug('no email address: ' + item['sid'])
                    self.new_curriculum_count.pop(item['sid'])

    def add_to_db_and_pop(self, sid):
        with self.connection.cursor() as cursor:
            for item in self.update_curriculum[sid]:
                cursor.execute(self.sql_update, (item['score'], item['cid'], item['sid']))
            self.update_curriculum.pop(sid)
            for item in self.new_curriculum[sid]:
                cursor.execute(self.sql_insert, (item['cid'], item['sid'], item['name'],
                                                 item['credit'], item['is_compulsory'], item['score'], 1))
            self.new_curriculum.pop(sid)
        self.connection.commit()

        if len(self.new_curriculum.items()) == 0 and len(self.update_curriculum.items()) == 0:
            self.connection.close()

    def pop_items(self, sid):
        self.new_curriculum.pop(sid)
        self.update_curriculum.pop(sid)

    @classmethod
    def get_email_by_sid(cls, sid, connection):
        sql = "SELECT name, email FROM `students_all` WHERE sid=%s"
        with connection.cursor() as cursor:
            cursor.execute(sql, (sid,))
            result = cursor.fetchone()
            return result
