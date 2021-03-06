# -*- coding: utf-8 -*-

import logging
import os

from tornado.escape import json_decode
from constants import EVENTER

from base import BaseHandler


class MainHandler(BaseHandler):

    def get(self):
        self.write("It works!")

    def post(self):
        """Put the body to correspongding queue(include position_queue, report_queue).
        """
        try:
            body = json_decode(self.request.body)
            if body['t'] == EVENTER.INFO_TYPE.POSITION:
                logging.debug("Get position request from sender:\n%s", body)
                self.position_queue.put(body)
                logging.info("Current position_queue size:%s, pid:%s", self.position_queue.qsize(), os.getpid())
            elif body['t'] == EVENTER.INFO_TYPE.REPORT:
                logging.debug("Get report request from sender:\n%s", body)
                self.report_queue.put(body)
                logging.info("Current report_queue size:%s, pid:%s", self.report_queue.qsize(), os.getpid())
            elif body['t'] == EVENTER.INFO_TYPE.CHARGE:
                logging.debug("Get charge request from sender:\n%s", body)
                self.position_queue.put(body)
                logging.info("Current position_queue size:%s, pid:%s", self.position_queue.qsize(), os.getpid())
            else:
                logging.warn("Get other request from sender:\n%s", body)
        except:
            logging.exception("[EVENTER] what's up")

