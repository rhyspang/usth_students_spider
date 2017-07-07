#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 17-7-7 下午6:48
# @Author  : rhys
# @Software: PyCharm
# @Project : students

import logging

from email.utils import COMMASPACE, formatdate, parseaddr, formataddr

import six
from scrapy.mail import MailSender, logger
from scrapy.signalmanager import SignalManager
from scrapy.utils.misc import arg_to_iter
from email.header import Header

from students.signals import email_sent_ok, email_sent_fail

if six.PY2:
    from email.MIMENonMultipart import MIMENonMultipart
    from email import Encoders, MIMEMultipart, MIMEText, MIMEBase
else:
    from email.mime.nonmultipart import MIMENonMultipart
    from email import encoders as Encoders

from twisted.internet import reactor

logger = logging.getLogger(__name__)


class MyMailSender(MailSender):
    def send(self, to, subject, body, cc=None, attachs=(), mimetype='text/plain', charset=None, _callback=None, sid=1):
        if attachs:
            msg = MIMEMultipart()
        else:
            msg = MIMENonMultipart(*mimetype.split('/', 1))

        to = list(arg_to_iter(to))
        cc = list(arg_to_iter(cc))

        msg['From'] = _format_addr(u'更新成绩自动推送 <%s>' % self.mailfrom)
        msg['To'] = COMMASPACE.join(to)
        msg['Date'] = formatdate(localtime=True)
        msg['Subject'] = subject
        rcpts = to[:]
        if cc:
            rcpts.extend(cc)
            msg['Cc'] = COMMASPACE.join(cc)

        if charset:
            msg.set_charset(charset)

        if attachs:
            msg.attach(MIMEText(body, 'plain', charset or 'us-ascii'))
            for attach_name, mimetype, f in attachs:
                part = MIMEBase(*mimetype.split('/'))
                part.set_payload(f.read())
                Encoders.encode_base64(part)
                part.add_header('Content-Disposition', 'attachment; filename="%s"' \
                                % attach_name)
                msg.attach(part)
        else:
            msg.set_payload(body)

        if _callback:
            _callback(to=to, subject=subject, body=body, cc=cc, attach=attachs, msg=msg)

        if self.debug:
            logger.debug('Debug mail sent OK: To=%(mailto)s Cc=%(mailcc)s '
                         'Subject="%(mailsubject)s" Attachs=%(mailattachs)d',
                         {'mailto': to, 'mailcc': cc, 'mailsubject': subject,
                          'mailattachs': len(attachs)})
            return

        dfd = self._sendmail(rcpts, msg.as_string())
        dfd.addCallbacks(self._sent_ok, self._sent_failed,
                         callbackArgs=[to, cc, subject, len(attachs), sid],
                         errbackArgs=[to, cc, subject, len(attachs), sid])
        reactor.addSystemEventTrigger('before', 'shutdown', lambda: dfd)
        return dfd

    def _sent_ok(self, result, to, cc, subject, nattachs, sid):
        super(MyMailSender, self)._sent_ok(result, to, cc, subject, nattachs)
        SignalManager().send_catch_log(email_sent_ok, sid=sid)

    def _sent_failed(self, failure, to, cc, subject, nattachs, sid):
        super(MyMailSender, self)._sent_failed(failure, to, cc, subject, nattachs)
        SignalManager().send_catch_log(email_sent_fail, sid=sid)


def _format_addr(s):
    name, addr = parseaddr(s)
    return formataddr((
        Header(name, 'utf-8').encode(),
        addr.encode('utf-8') if isinstance(addr, unicode) else addr))
