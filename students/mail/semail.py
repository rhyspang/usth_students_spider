#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 17-6-23 下午5:39
# @Author  : rhys
# @Software: PyCharm
# @Project : students

from scrapy.signalmanager import SignalManager
from twisted.internet import reactor

from students.mail.mail import MyMailSender
from students.signals import email_sent_ok, email_sent_fail

body1 = u"""
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" 
"http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html lang="cn">

<head>
    <meta charset="utf-8">

    
</head>
<body>

<!-- CSS goes in the document HEAD or added to your external stylesheet -->
    <style type="text/css">
    table.altrowstable {
        font-family: verdana, arial, sans-serif;
        font-size: 11px;
        color: #333333;
        border-width: 1px;
        border-color: #a9c6c9;
        border-collapse: collapse;
    }

    table.altrowstable th {
        border-width: 1px;
        padding: 8px;
        border-style: solid;
        border-color: #a9c6c9;
    }

    table.altrowstable td {
        border-width: 1px;
        padding: 8px;
        border-style: solid;
        border-color: #a9c6c9;
    }

    .oddrowcolor {
        background-color: #d4e3e5;
    }

    .evenrowcolor {
        background-color: #c3dde0;
    }
    </style>

"""

table_header = u"""
    <!-- Table goes in the document BODY -->
    <table class="altrowstable" id="alternatecolor">
        <tr>
            <th>课程名称</th>
         
            <th>分数</th>
        </tr>
"""

table_footer = u"""
</table>
"""

footer_sec = u"""
</body>

</html>

"""

title_template = u"""
<strong>{}</strong>,你好:<br>
"""

table_template = u"""
        <tr>
            <td>{}</td>
            <td>{}</td>
        </tr>
"""


def send_message(email, new_curriculum_list, update_curriculum_list, name, spider, sid):
    title = title_template.format(name)
    if new_curriculum_list:
        new_curriculum_table = ''.join([table_template.format(curriculum['name'],

                                                              curriculum['score'])
                                        for curriculum in new_curriculum_list])
    if update_curriculum_list:
        update_curriculum_table = ''.join([table_template.format(curriculum['name'],

                                                                 curriculum['score'])
                                           for curriculum in update_curriculum_list])
    body = body1 + title
    if new_curriculum_list:
        body += u'新出成绩:<br>' + table_header + new_curriculum_table + table_footer
    if update_curriculum_list:
        body += u'更新成绩:<br>' + table_header + update_curriculum_table + table_footer
    body += footer_sec

    mailer = MyMailSender.from_settings(spider.settings)

    subject = u"出成绩了！！！"

    mailer.send(to=[email],
                subject=subject,
                body=body.encode('utf-8'),
                mimetype='text/HTML',
                cc=['rhyspang@qq.com'],
                sid=sid)
