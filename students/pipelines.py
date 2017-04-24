# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

import pymysql


class StudentsPipeline(object):
    def process_item(self, item, spider):
        db_config = spider.settings.get('MYSQL_DB_KWARGS')
        connection = pymysql.connect(**db_config)
        try:
            with connection.cursor() as cursor:
                # Create a new record
                sql = "INSERT INTO `students` " \
                      "(`sid`, `name`, `id`, `gender`, " \
                      "`college`, `class_name`,`nationality`, " \
                      "`tel`, `email`) " \
                      "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
                cursor.execute(sql, (item['sid'], item['name'], item['id'],
                                     0 if item['gender'] == '女' else 1, item['college'], item['class_name'],
                                     item['nationality'], item['tel'], item['email']))

            # connection is not autocommit by default. So you must commit to save
            # your changes.
            connection.commit()

        finally:
            connection.close()

        return item
