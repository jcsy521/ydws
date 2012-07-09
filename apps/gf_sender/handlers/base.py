# -*- coding: utf-8 -*-

import tornado.web
from tornado.escape import json_decode


class BaseHandler(tornado.web.RequestHandler):
    
    SUPPORTED_METHODS = ("GET", "POST")

    JSON_HEADER = ("Content-Type", "application/json; charset=utf-8")
    
    @property
    def sender(self):
        return self.application.gf_sender

    @tornado.web.removeslash
    def post(self):
        args = json_decode(self.request.body)
        getattr(self, 'do_%s' % args['method'].lower())(args)
