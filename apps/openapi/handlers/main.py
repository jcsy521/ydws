# -*- coding: utf-8 -*-

import logging

from base import BaseHandler


class MainHandler(BaseHandler):

    def get(self):
        self.write("It works!")
      
