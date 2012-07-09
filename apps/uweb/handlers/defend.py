# -*- coding: utf-8 -*-

import logging
import datetime
import time
from dateutil.relativedelta import relativedelta

from tornado.escape import json_decode, json_encode
import tornado.web
from tornado.ioloop import IOLoop

from helpers.seqgenerator import SeqGenerator
from helpers.gfsenderhelper import GFSenderHelper
from utils.misc import get_today_last_month
from utils.dotdict import DotDict
from base import BaseHandler, authenticated
from codes.errorcode import ErrorCode
from constants import UWEB


class DefendHandler(BaseHandler):

    @authenticated
    @tornado.web.removeslash
    @tornado.web.asynchronous
    def post(self):
        status = ErrorCode.SUCCESS
        try:
            res = self.db.get("SELECT defend_status"
                              "  FROM T_TERMINAL_INFO_W"
                              "  WHERE tid = %s",
                              self.current_user.tid)
        except Exception as e:
            logging.exception("Set terminal failed. Exception: %s", e.args)
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)
            IOLoop.instance().add_callback(self.finish)
            return 

        def _on_finish(response):
            
            status = ErrorCode.SUCCESS

            response = json_decode(response)
            if response['success'] == 0:
                defend_status = UWEB.DEFEND_STATUS.YES 
                if res.defend_status == UWEB.DEFEND_STATUS.YES:
                    defend_status = UWEB.DEFEND_STATUS.NO
                elif res.defend_status == UWEB.DEFEND_STATUS.NO:  
                    pass
                else: 
                    logging.error("Unknown defend_status: %s", res.defend_status)
                    status = ErrorCode.SERVER_ERROR
                self.db.execute("UPDATE T_TERMINAL_INFO_W"
                                "  SET defend_status = %s"
                                "  WHERE tid = %s",
                                defend_status, self.current_user.tid)
            else:
                status = response['success'] 
                logging.error('Set defend_status failed. status: %s, message: %s', status, ErrorCode.ERROR_MESSAGE[status] )
            self.write_ret(status)
            IOLoop.instance().add_callback(self.finish)

        try:
            if res.defend_status == UWEB.DEFEND_STATUS.YES:
                args = DotDict(seq=SeqGenerator.next(self.db),
                               tid=self.current_user.tid,
                               defend_status=UWEB.DEFEND_STATUS.NO)

                logging.info("set defend_status from Yes to No")
                GFSenderHelper.async_forward(GFSenderHelper.URLS.DEFEND, args,
                                                  _on_finish)
            elif res.defend_status == UWEB.DEFEND_STATUS.NO:
                args = DotDict(seq=SeqGenerator.next(self.db),
                               tid=self.current_user.tid,
                               defend_status=UWEB.DEFEND_STATUS.YES)

                logging.info("set defend_status from No to Yes")
                GFSenderHelper.async_forward(GFSenderHelper.URLS.DEFEND, args,
                                                  _on_finish)
            else:
                # NOTE: in fact, this branch should be never used.
                logging.error("Unknown defend_status: %s", res.defend_status)
                raise Exception("Unknown defend_status: %s" % res.defend_status)
        except Exception as e:
            logging.exception("Set defend_status failed. Exception: %s", e.args)
            status = ErrorCode.SERVER_ERROR
            self.write_ret(status)
            IOLoop.instance().add_callback(self.finish)
