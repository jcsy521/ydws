# -*- coding: utf-8 -*-

import logging
import time

from tornado.escape import json_decode, json_encode
import tornado.web
from tornado.ioloop import IOLoop

from helpers.seqgenerator import SeqGenerator
from helpers.gfsenderhelper import GFSenderHelper
from helpers.queryhelper import QueryHelper
from utils.misc import get_terminal_info_key 
from utils.dotdict import DotDict
from codes.errorcode import ErrorCode
from constants import UWEB 

from base import BaseHandler, authenticated
from mixin.base import BaseMixin


class DefendHandler(BaseHandler, BaseMixin):

    @authenticated
    @tornado.web.removeslash
    def get(self):
        status = ErrorCode.SUCCESS
        try:
            tid = self.get_argument('tid',None) 
            # check tid whether exist in request and update current_user
            self.check_tid(tid)
            
            terminal = self.db.get("SELECT fob_status, mannual_status, defend_status"
                                   "  FROM T_TERMINAL_INFO"
                                   "  WHERE tid = %s"
                                   "    AND service_status = %s",
                                   self.current_user.tid,
                                   UWEB.SERVICE_STATUS.ON)
            if not terminal:
                status = ErrorCode.LOGIN_AGAIN
                logging.error("The terminal with tid: %s does not exist, redirect to login.html", self.current_user.tid)
                self.write_ret(status)
                return
            else:
                terminal_info_key = get_terminal_info_key(self.current_user.tid)
                terminal_info = self.redis.getvalue(terminal_info_key)
                if terminal['mannual_status'] != terminal_info['mannual_status']:
                    terminal_info['mannual_status'] = terminal['mannual_status'] 
                    self.redis.setvalue(terminal_info_key, terminal_info)
                    logging.error("[UWEB] the mannual_status in redis is not same as in database, update it")

            self.write_ret(status,
                           dict_=DotDict(defend_status=terminal.defend_status, 
                                         mannual_status=terminal.mannual_status,
                                         fob_status=terminal.fob_status))
        except Exception as e:
            logging.exception("[UWEB] uid:%s tid:%s get defend status failed. Exception: %s", 
                              self.current_user.uid, self.current_user.tid, e.args)
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)
            return 

    @authenticated
    @tornado.web.removeslash
    def post(self):
        status = ErrorCode.SUCCESS
        try:
            data = DotDict(json_decode(self.request.body))
            tid = data.get('tid', None) 
            tids = data.get('tids', None)
            # check tid whether exist in request and update current_user
            self.check_tid(tid)
            logging.info("[UWEB] defend request: %s, uid: %s, tid: %s, tids: %s", 
                         data, self.current_user.uid, self.current_user.tid, tids)
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            self.write_ret(status)
            return 

        try:
            for tid in tids:
                terminal = self.db.get("SELECT id FROM T_TERMINAL_INFO"
                                       "  WHERE tid = %s"
                                       "    AND service_status = %s",
                                       tid, UWEB.SERVICE_STATUS.ON)
                if not terminal:
                    status = ErrorCode.LOGIN_AGAIN
                    logging.error("The terminal with tid: %s does not exist, redirect to login.html", tid)
                    self.write_ret(status)
                    return

                #self.keep_waking(self.current_user.sim, self.current_user.tid)
                self.db.execute("UPDATE T_TERMINAL_INFO"
                                "  SET mannual_status = %s"
                                "  WHERE tid = %s",
                                data.mannual_status, tid)

                terminal_info_key = get_terminal_info_key(tid)
                terminal_info = self.redis.getvalue(terminal_info_key)
                if terminal_info:
                    terminal_info['mannual_status'] = data.mannual_status
                    self.redis.setvalue(terminal_info_key, terminal_info)
                logging.info("[UWEB] uid:%s, tid:%s set mannual status to %s successfully", 
                             self.current_user.uid, tid, data.mannual_status)
            self.write_ret(status)
        except Exception as e:
            logging.exception("[UWEB] uid:%s, tid:%s set mannual status to %s failed. Exception: %s", 
                              self.current_user.uid, self.current_user.tid, data.mannual_status, e.args)
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)
