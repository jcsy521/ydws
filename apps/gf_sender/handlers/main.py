# -*- coding: utf-8 -*-

from base import BaseHandler


class MainHandler(BaseHandler):

    def get(self):
        self.write("It works!")

