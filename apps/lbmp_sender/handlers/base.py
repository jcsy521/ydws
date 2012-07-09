# -*- coding: utf-8 -*-

import httplib2
import errno, time

import tornado.web
from helpers.confhelper import ConfHelper

class BaseHandler(tornado.web.RequestHandler):
    
    # override the attribute
    SUPPORTED_METHODS = ("POST",)

    JSON_HEADER = {"Content-Type": "application/json; charset=utf-8"} 

    def __init__(self, application, request): 
        tornado.web.RequestHandler.__init__(self, application, request)

    @property
    def queue(self):
        return self.application.queue
 
    @property
    def http(self):
        return httplib2.Http(".lbmp_cache")
