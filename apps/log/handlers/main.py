#!/usr/bin/python
# -*- coding: UTF-8 -*-

import tornado.database

from base import authenticated

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.redirect("/login") 
