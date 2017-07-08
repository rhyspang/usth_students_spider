#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 17-6-23 下午5:39
# @Author  : rhys
# @Software: PyCharm
# @Project : students
from datetime import datetime
from students.mail.mail import MyMailSender
from jinja2 import Environment, PackageLoader


def send_message(email, new_curriculum_list, update_curriculum_list, name, spider, sid):
    env = Environment(loader=PackageLoader('students.mail', 'templates'))
    template = env.get_template('mail.html')
    body = template.render({'name': name,
                            'new_items': new_curriculum_list,
                            'update_items': update_curriculum_list,
                            'date': datetime.now()})

    mailer = MyMailSender.from_settings(spider.settings)

    subject = u"出成绩了！！！"

    mailer.send(to=[email],
                subject=subject,
                body=body.encode('utf-8'),
                mimetype='text/HTML',
                cc=['rhyspang@qq.com'],
                sid=sid)
