# -*- coding: utf-8 -*-

import logging

from base import BaseHandler


class MainHandler(BaseHandler):

    def get(self):
        self.write("It works!")

    def post(self):
        # en, there should be a dispatcher for different types. no
        # more than 10 lines codes here, otherwise, it's doomed to suck!
        logging.debug("Get request from sender:\n%s", self.request.body)
        if self.request.body:
            self.queue.put(self.request.body)


