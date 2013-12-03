#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib2
import urllib
import logging
import re
import os.path
import site
import sys
from tornado.escape import json_decode

TOP_DIR_ = os.path.abspath(os.path.join(__file__, "../../../../.."))
site.addsitedir(os.path.join(TOP_DIR_, "libs"))

from codes.errorcode import ErrorCode


class HttpClient(object):
    reload(sys)          
    sys.setdefaultencoding('utf-8')
    
    def send_http_post_request(self, url= None, data=None, encoding='utf-8'):
        """
        Send the packet to sms service and receive the result.
        @return: {
                   status:xxx,
                   message:xxx,
                 }
        """
        status = ErrorCode.SUCCESS
        message = '' 
        f = None
        try: 
            # Definition request object
            request = urllib2.Request(url)  
            # uid=2590&msg=%E4%BD%A0%E5%A5%BD+%E5%88%98%E6%97%B6%E5%98%89%EF%BC%81&msgid=53970002&cmd=send&psw=CEE712A91DD4D0A8A67CC8E47B645662&mobiles=15010955397
            request.add_data(urllib.urlencode(data))
            request.add_header("Content-type", "application/x-www-form-urlencoded")
            # Open the url and return the object that likes a file
            f = urllib2.urlopen(request)  
            response = f.read()
            if int(response) != 0:
                status = ErrorCode.FAILED
        except urllib2.HTTPError, msg:
            status = ErrorCode.FAILED
            logging.exception("Connection sms service HTTPError : %s", msg)
        except urllib2.URLError, msg:
            status = ErrorCode.FAILED
            logging.exception("Connection sms service URLError : %s", msg)
        except Exception, msg:
            status = ErrorCode.FAILED
            logging.exception("Send http post request exception : %s", msg)
        finally:
            if f:
                f.close()
            
            ret = dict(status=status, 
                       message=ErrorCode.ERROR_MESSAGE[status])
            return ret


if __name__ == "__main__":
    data = dict(cmd="send",
                uid="2590",
                psw="CEE712A91DD4D0A8A67CC8E47B645662",
                mobile="18611357615",
                msgid="76150006",
                content=u"你好 ！".encode('utf8'))
    httpclient = HttpClient()
    url = 'http://192.168.1.9:8005/cmpp_sms/SendService'
    ret = httpclient.send_http_post_request(url, data)
    print ret
