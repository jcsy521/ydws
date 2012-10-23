# -*- coding: utf-8 -*-

import logging
import httplib
import errno, time

import tornado.web
from helpers.confhelper import ConfHelper
from constants import HTTP, LBMP
from utils.dotdict import DotDict

class BaseHandler(tornado.web.RequestHandler):
    
    # override the attribute
    SUPPORTED_METHODS = ("POST",)

    JSON_HEADER = {"Content-Type": "application/json; charset=utf-8"} 

    def __init__(self, application, request): 
        tornado.web.RequestHandler.__init__(self, application, request)

    @property
    def queue(self):
        return self.application.queue

    def send(self, host, url, args, method=HTTP.METHOD.POST):
        """
        Send the packet with args to url.
        """
        assert ConfHelper.loaded

        DUMMY_RESPONSE = LBMP.DUMMY

        if method.upper() not in HTTP.METHOD:
            return DUMMY_RESPONSE
        else:
            MAXIMUM_NUMBER_OF_ATTEMPTS = 2
            ret = DUMMY_RESPONSE
            for attempt in range(MAXIMUM_NUMBER_OF_ATTEMPTS):
                try:
                    connection = httplib.HTTPConnection(host,
                                                        timeout=HTTP.ASYNC_REQUEST_TIMEOUT)
                    connection.request(method, url, args)
                    response = connection.getresponse()
                    if response.status == 200:
                        ret = response.read() 
                    connection.close()
                except EnvironmentError as exc:
                    if exc.errno == errno.ECONNREFUSED:
                        logging.info("Connection refused, try connect again...")
                        time.sleep(1)
                    else:
                        logging.exception("Environment error:%s", exc.args[0])
                        break
                except Exception as e:
                    logging.exception("Request exception:%s", e.args[0])
                    break
                else:
                    break
            return ret 
