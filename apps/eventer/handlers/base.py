# -*- coding: utf-8 -*-

import tornado.web


class BaseHandler(tornado.web.RequestHandler):

    @property
    def position_queue(self):
        return self.application.position_queue

    @property
    def report_queue(self):
        return self.application.report_queue

