# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
import math
import pymysql
from students.items import Curriculum, StudentItem
from students.semail import send_message


class StudentsPipeline(object):
    def __init__(self, db_config):
        self.connection = None
        self.db_config = db_config

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            db_config=crawler.settings.get('MYSQL_DB_KWARGS')
        )

    def open_spider(self, spider):
        self.connection = pymysql.connect(**self.db_config)

    def close_spider(self, spider):
        self.connection.close()

    def process_item(self, item, spider):
        connection = self.connection
        with connection.cursor() as cursor:
            self.save_student(item, cursor)
        connection.commit()
        return item

    @staticmethod
    def save_student(item, cursor):
        if not isinstance(item, StudentItem):
            return

        if item.get('name') == 'null':
            return

        sql_insert_item = "INSERT INTO `students_all` " \
                          "(`sid`, `name`, `id`, `gender`, " \
                          "`college`, `class_name`,`nationality`, " \
                          "`tel`, `email`, `password`) " \
                          "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        sql_insert_sid = "INSERT INTO `students_all`(`sid`) VALUES (%s)"
        sql_update = "UPDATE `students_all` SET " \
                     "`id`=%s, `name`=%s, `gender`=%s, " \
                     "`college`=%s, `class_name`=%s,`nationality`=%s, " \
                     "`tel`=%s, `email`=%s, `password`=%s " \
                     "WHERE sid=%s"
        sql_select = "SELECT * FROM `students_all` WHERE sid=%s"

        cursor.execute(sql_select, (item['sid'],))

        has_record = True if cursor.fetchone() else False

        if item.get('name'):
            if has_record:
                cursor.execute(sql_update, [item.get('id'), item.get('name'), item.get('gender'),
                                            item.get('college'), item.get('class_name'), item.get('nationality'),
                                            item.get('tel'), item.get('email'), item.get('password'),
                                            item.get('sid')])
            else:
                cursor.execute(sql_insert_item, (item.get('sid'), item.get('name'), item.get('id'),
                                                 item.get('gender'), item.get('college'), item.get('class_name'),
                                                 item.get('nationality'), item.get('tel'), item.get('email'),
                                                 item.get('password')))
        else:
            if not has_record:
                cursor.execute(sql_insert_sid, (item['sid'],))


class CurriculumPipeline(object):
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
        return cls(
            db_config=crawler.settings.get('MYSQL_DB_KWARGS')
        )

    def open_spider(self, spider):
        self.connection = pymysql.connect(**self.db_config)

    def close_spider(self, spider):
        self.connection.close()

    def process_item(self, item, spider):
        connection = self.connection
        with connection.cursor() as cursor:
            self.save_curriculum(item, cursor, spider)
        connection.commit()
        return item

    def save_curriculum(self, item, cursor, spider):
        if not isinstance(item, Curriculum):
            return
        sql_insert = "INSERT INTO `curriculum_all` " \
                     "(`cid`, `sid`, `name`, " \
                     "`credit`, `is_compulsory`, `score`, `is_new`, `update_date`) " \
                     "VALUES (%s, %s, %s, %s, %s, %s, %s, now())"
        sql_select = "SELECT score FROM `curriculum_all` WHERE cid=%s AND sid=%s"
        sql_update = "UPDATE `curriculum_all` SET `score`=%s, `update_date`=now() WHERE cid=%s AND sid=%s"

        cursor.execute(sql_select, (item['cid'], item['sid']))
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
            cursor.execute(sql_update, (item['score'], item['cid'], item['sid']))
        # 数据表中没有查询到的记录
        else:
            self.new_curriculum[item['sid']].append(item)
            cursor.execute(sql_insert, (item['cid'], item['sid'], item['name'],
                                        item['credit'], item['is_compulsory'], item['score'], 1))

        # 当成绩页面上的成绩条目都检索完时,
        if self.new_curriculum_count[item['sid']] == int(item['all']):
            if self.new_curriculum.get(item['sid']) or self.update_curriculum.get(item['sid']):
                name, email = self.get_email_by_sid(item['sid'], self.connection)
                if email.strip():
                    send_message(email,
                                 self.new_curriculum[item['sid']],
                                 self.update_curriculum[item['sid']],
                                 name,
                                 spider)
                    spider.logger.debug("item['sid']" + 'send email to: ' + email)
                else:
                    spider.logger.debug('no email address: ' + item['sid'])
                self.new_curriculum.pop(item['sid'])

            self.new_curriculum_count.pop(item['sid'])

    @classmethod
    def get_email_by_sid(cls, sid, connection):
        sql = "SELECT name, email FROM `students_all` WHERE sid=%s"
        with connection.cursor() as cursor:
            cursor.execute(sql, (sid,))
            result = cursor.fetchone()
            return result
