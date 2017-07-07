#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 17-7-7 下午6:32
# @Author  : rhys
# @Software: PyCharm
# @Project : students
import pymysql

from students.items import StudentItem


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
