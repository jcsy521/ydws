# -*- coding: utf-8 -*-

from urllib import urlencode
import urllib2 
import logging
import time
import re

from confhelper import ConfHelper
from utils.misc import safe_utf8
from codes.errorcode import ErrorCode
from tornado.escape import json_decode, json_encode


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

    @classmethod
    def send_to_terminal(cls, tmobile, content):
        """
        @param tmobile: mobile of terminal
        @param content: original sms content
        authentic content: xxx sign timestamp
            - xxx: original sms content
            - sign: (last 8 nums of tmobile) ^ SEND_KEY ^ timestamp
            - timestamp: unix time
        """
        send_key = int(ConfHelper.SMS_CONF.send_key, 16)
        timestamp = int(time.time())
        sign = int(str(tmobile)[-8:]) ^ (send_key) ^ timestamp
        content = ' '.join([content, str(sign), str(timestamp)])

        #NOTE: check whether send throught sms_cmpp
        #cmpp_pattern = r":SIM|:JB|:CQ|:LQGZ"      
        nosign = 1
        response = cls.send(tmobile, content, nosign)

        return response

    @classmethod
    def send_update_to_terminal(cls, tmobile, content):
        """
        @param tmobile: mobile of terminal
        @param content: original sms content
        authentic content: xxx sign timestamp
            - xxx: original sms content
            - sign: (last 8 nums of tmobile) ^ SEND_KEY ^ timestamp
            - timestamp: unix time
        """
        send_key = int(ConfHelper.SMS_CONF.send_key, 16)
        timestamp = int(time.time())
        sign = int(str(13800138000)[-8:]) ^ (send_key) ^ timestamp
        content = ' '.join([content, str(sign), str(timestamp)])
           
        response = cls.send(tmobile, content)

        return response

    @staticmethod
    def send(mobile, content, nosign=0):
        """
        @param mobile: send to whom
        @param content: what to send
        @param is_cmpp: whether use sms_cmpp

        @return response: str,
                { 
                 'status':int 0:success,-1:failed.
                 'msgid': 
                }
        """
        status = ErrorCode.SUCCESS 
        response = dict(status=status, 
                        message=ErrorCode.ERROR_MESSAGE[status],
                        msgid=1111)
        response = json_encode(response) 
        return response

        response = None
        f = None
        logging.info("[SMS] mobile=%s, content=%s, nosign:%s", mobile, content, nosign)
        try:
            content = safe_utf8(content)

            req = urllib2.Request(url=ConfHelper.SMS_CONF.sms_url,
                                  data=urlencode(dict(mobile=mobile,
                                                      content=content,
                                                      nosign=nosign)))
            f = urllib2.urlopen(req)
            response = f.read()
        except urllib2.URLError as e:
            logging.error("URLError: %s", e.args)
        except Exception as e:
            logging.error("Unknow error: %s", e.args)
        finally:
            if f:
                f.close()
        return response 


