# -*- coding: utf-8 -*-

import tornado.web


class BaseHandler(tornado.web.RequestHandler):

    @property
    def queue(self):
        return self.application.queue
