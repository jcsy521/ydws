#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib2
import urllib
import logging
import re
import os.path
import site
from tornado.httpclient import AsyncHTTPClient
from tornado.httpclient import HTTPRequest, HTTPResponse

TOP_DIR_ = os.path.abspath(os.path.join(__file__, "../../../.."))
site.addsitedir(os.path.join(TOP_DIR_, "libs"))

from codes.errorcode import ErrorCode


class HttpClient(object):

    def async_send_http_post_request(self, url = None, data = None, callback = None, encoding = 'utf-8'):
        _CONTENT_TYPE = {"Content-type": "text/xml; charset=utf-8"}
        ASYNC_CLIENT = AsyncHTTPClient(max_clients=500)
        status = ErrorCode.SUCCESS

        def _callback(response):
            data = {"status" : ErrorCode.SUCCESS, "response" : response}
            callback(data)

        req = HTTPRequest(url,
                          method='POST',
                          headers=_CONTENT_TYPE,
                          body=json_encode(data),
                          connect_timeout=30,
                          request_timeout=30)
        ASYNC_CLIENT.fetch(req, _callback)
    
    def send_http_post_request(self, url = None, data = None, encoding = 'utf-8'):
        """
        Send the packet to sms service and receive the result.
        """
        opener = None
        status = ErrorCode.SUCCESS
        response = None
        try: 
            # Definition request object
            request = urllib2.Request(url)  
            request.add_data(data)
            request.add_header("Content-type", "text/xml")
            # Open the url and return the object that likes a file
            opener = urllib2.urlopen(request)  
            if opener:
                # Get opener text  
                streamData = "" 
                while True:  
                    subData = opener.read(2048)  
                    if subData == "":  
                        break  
                    streamData = streamData + subData  
            
                response = streamData.decode('utf-8')
            else:
                logging.error("Opener is None")
                
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
            if opener:
                opener.close()
            return {"status" : status, "response" : response}

