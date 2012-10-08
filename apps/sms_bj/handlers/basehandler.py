#!/usr/bin/env python
# -*- coding: utf-8 -*-

import tornado.web


class _DBDescriptor(object):
    def __get__(self, obj, type=None):
        return obj.application.db


class BaseHandler(tornado.web.RequestHandler):

    SUPPORTED_METHODS = ("GET", "POST")

    # NOTE: use descriptor for db in order to override it in thread callbacks.
    db = _DBDescriptor()
    
#    @property
#    def db(self):
#        return self.application.db