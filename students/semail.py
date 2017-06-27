#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 17-6-23 下午5:39
# @Author  : rhys
# @Software: PyCharm
# @Project : students
from email.header import Header
from email.utils import parseaddr, formataddr

from scrapy.mail import MailSender

body1 = u"""
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" 
"http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html lang="cn">

<head>
    <meta charset="utf-8">

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
</head>

<body>
    <!-- Table goes in the document BODY -->
    <table class="altrowstable" id="alternatecolor">
        <tr>
            <th>课程名称</th>
            <th>学分</th>
            <th>分数</th>
        </tr>
"""

body3 = u"""
    </table>
</body>

</html>

"""

title_template = u"""
{}同学,你好:
"""

body2_template = u"""
        <tr>
            <td>{}</td>
            <td>{}</td>
            <td>{}</td>
        </tr>
"""


def send_message(email, curriculumn_list, name, spider):
    title = title_template.format(name)
    body2 = ''.join([body2_template.format(curriculumn['name'],
                                           curriculumn['credit'],
                                           curriculumn['score'])
                     for curriculumn in curriculumn_list])
    body = body1 + title + body2 + body3

    mailer = MailSender.from_settings(spider.settings)

    subject = "出成绩了！！！"
    mailer.send(to=[email],
                subject=subject,
                body=body.encode('utf-8'),
                mimetype='text/HTML',
                cc=['rhyspang@qq.com'])


def _format_addr(s):
    name, addr = parseaddr(s)
    return formataddr((
        Header(name, 'utf-8').encode(),
        addr.encode('utf-8') if isinstance(addr, unicode) else addr))
