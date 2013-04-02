# -*- coding: utf-8 -*-

import logging
import smtplib

from confhelper import ConfHelper
from utils.misc import safe_utf8


class EmailHelper:
    """Send email, and someone else receives email."""

    @staticmethod
    def send(email, content):
        """
        @param mobile: send to whom
        @param content: what to send

        @return response: str,
                { 
                 'status':int 0:success,-1:failed.
                 'msgid': 
                }
        """
        logging.info("email=%s, content=%s", email, content)
        text = "From:%s\r\nTo:%s\r\nSubject:%s\r\n\r\n%s"
        text = text % (ConfHelper.EMAIL_CONF.efrom,
                       email,
                       ConfHelper.EMAIL_CONF.subject,
                       content)
        text = safe_utf8(text)

        senderrs = None
        try:
            smtp = smtplib.SMTP()
            smtp.connect(ConfHelper.EMAIL_CONF.server)
            #smtp.ehlo()
            #smtp.starttls()
            smtp.login(ConfHelper.EMAIL_CONF.user, ConfHelper.EMAIL_CONF.password)
            senderrs = smtp.sendmail(ConfHelper.EMAIL_CONF.user, email, text)
            smtp.quit()
        except Exception as e:
            senderrs = e.args[0]
            logging.error("Unknow error: %s", e.args)

        return senderrs
            
