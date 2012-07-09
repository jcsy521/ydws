# -*- coding: utf-8 -*-

from urllib import urlencode
import urllib2 
import logging

from confhelper import ConfHelper
from utils.misc import safe_utf8


class SMSHelper:
    """Send sms, and someone else receives sms."""

    # max length of a sms in bytes
    MAX_LENGTH = 70

    # sms is encoded in UCS2.
    SMS_ENCODING = "UTF-16-BE"
    # the BOM
    HEADER_LEN = 2
    # the final mark (NULL now)
    TAIL_LEN = 0

    @classmethod
    def sms_encode(cls, content):
        assert isinstance(content, unicode)
        return content.encode(cls.SMS_ENCODING)

    @classmethod
    def sms_length(cls, content):
        return len(cls.sms_encode(content))

    @classmethod
    def check_sms_length(cls, content):
        return (cls.HEADER_LEN + 
                cls.sms_length(content) + 
                cls.TAIL_LEN) <= cls.MAX_LENGTH

    @staticmethod
    def send(mobile, content):
        """
        @param mobile: send to whom
        @param content: what to send

        @return  True: send ok
                False: fails
        """
        logging.debug("mobile=%s, content=%s", mobile, content)

        content = safe_utf8(content)

        send_ok = False
        try:
            req = urllib2.Request(url=ConfHelper.SMS_CONF.url,
                                  data=urlencode(dict(mobile=mobile,
                                                      content=content)))
            f = urllib2.urlopen(req)
            response = f.read()
            f.close()
        except urllib2.URLError as e:
            logging.error("URLError: %s", e.args)
        except Exception as e:
            logging.error("Unknow error: %s", e.args)
        else:
            # contract with the sms gateway
            # 0: success
            # other: failse
            if response == '0':
                send_ok = True
            
        # return send_ok
        return True 
