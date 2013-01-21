# -*- coding: utf-8 -*-

import logging

import tornado.web

from constants import UWEB
from base import BaseHandler

class HelperHandler(BaseHandler):

    @tornado.web.removeslash
    def get(self):
        """Jump to the coresponding help.html."""
        user_type = self.get_argument('user_type',UWEB.USER_TYPE.PERSON)
        if user_type == UWEB.USER_TYPE.PERSON:
            self.render('helper.html')
        else:
            self.render('helper_corp.html')

