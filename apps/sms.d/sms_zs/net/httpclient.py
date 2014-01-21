#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib2
import urllib
import logging
import re
import os.path
import site

TOP_DIR_ = os.path.abspath(os.path.join(__file__, "../../../.."))
site.addsitedir(os.path.join(TOP_DIR_, "libs"))

from codes.errorcode import ErrorCode


class HttpClient(object):
    
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
                logging.error("[SMS] Opener is None")
                
        except urllib2.HTTPError, msg:
            status = ErrorCode.FAILED
            logging.exception("[SMS] Connection sms service HTTPError : %s", msg)
        except urllib2.URLError, msg:
            status = ErrorCode.FAILED
            logging.exception("[SMS] Connection sms service URLError : %s", msg)
        except Exception, msg:
            status = ErrorCode.FAILED
            logging.exception("[SMS] Send http post request exception : %s", msg)
        finally:
            if opener:
                opener.close()
            return {"status" : status, "response" : response}
