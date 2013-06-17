# -*- coding: utf-8 -*-

import logging
import smtplib
import os

from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.utils import COMMASPACE,formatdate
from email import encoders

from confhelper import ConfHelper
from utils.misc import safe_utf8


class EmailHelper:
    """Send email, and someone else receives email."""

    @staticmethod
    def send(to_email, content, cc_email=[], files=[]):
        """
        @param to_email: list, emails to be sent to
        @param cc_email: list, emails to be copy to
        @param content: str, what to send
        @param files: list, the attachements to be sent

        @return response: str,
                { 
                 'status':int 0:success,-1:failed.
                 'msgid': 
                }
        """
        logging.info("to_email=%s, cc_email=%s, content=%s", to_email, cc_email, content)
        #text = "From:%s\r\nTo:%s\r\nSubject:%s\r\n\r\n%s"
        #text = text % (ConfHelper.EMAIL_CONF.efrom,
        #               email,
        #               ConfHelper.EMAIL_CONF.subject,
        #               content)
        #text = safe_utf8(text)
        if type(to_email) != list:
            to_email = [to_email,]
        
        msg = MIMEMultipart() 
        msg['From'] = ConfHelper.EMAIL_CONF.efrom
        msg['Subject'] = ConfHelper.EMAIL_CONF.subject 
        msg['To'] = COMMASPACE.join(to_email) 
        if cc_email:
            msg['Cc'] = COMMASPACE.join(cc_email) 
        msg['Date'] = formatdate(localtime=True) 
        msg.attach(MIMEText(safe_utf8(content))) 

        for file in files: 
            part = MIMEBase('application', 'octet-stream') #'octet-stream': binary data 
            part.set_payload(open(file, 'rb').read()) 
            encoders.encode_base64(part) 
            part.add_header('Content-Disposition', 'attachment; filename="%s"' % os.path.basename(file)) 
            msg.attach(part) 

        senderrs = None
        try:
            smtp = smtplib.SMTP()
            smtp.connect(ConfHelper.EMAIL_CONF.server)
            #smtp.ehlo()
            #smtp.starttls()
            smtp.login(ConfHelper.EMAIL_CONF.user, ConfHelper.EMAIL_CONF.password)

            senderrs = smtp.sendmail(ConfHelper.EMAIL_CONF.user, to_email+cc_email, msg.as_string())
            smtp.quit()
        except Exception as e:
            senderrs = e.args[0]
            logging.error("Unknow error: %s", e.args)

        return senderrs
