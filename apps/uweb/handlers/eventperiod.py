# -*- coding: utf-8 -*-

"""This module is designed for eventer-period .

NOTE: deprecated.
"""

import logging

from tornado.escape import json_decode
import tornado.web

from utils.dotdict import DotDict
from codes.errorcode import ErrorCode
from base import BaseHandler, authenticated

class EventPeriodHandler(BaseHandler):

    @authenticated
    @tornado.web.removeslash
    def get(self):
        status = ErrorCode.SUCCESS
        try:
            tid = self.get_argument('tid')
            alerts = self.db.query("SELECT * FROM T_ALERT_SETTING WHERE tid=%s", 
                                   tid)
            self.write_ret(status,dict_=dict(res=alerts))
        except Exception as e:
            status = ErrorCode.FAILED
            logging.exception("[UWEB] tid:%s get event period failed. Exception:%s", 
                              tid, e.args)
            self.write_ret(status)

    @authenticated
    @tornado.web.removeslash
    def post(self):
        status = ErrorCode.SUCCESS
        try:
            data = DotDict(json_decode(self.request.body))
            tid = data.get("tid", None)
            self.check_tid(tid)
            logging.info("[UWEB] terminal request: %s, uid: %s, tid: %s", 
                         data, self.current_user.uid, self.current_user.tid)
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            self.write(status)
            return

        try:
            tid = data["tid"]
            items = self.db.query("SELECT * FROM T_ALERT_SETTING WHERE tid=%s", tid)
            if len(items) >= 7:
                status = ErrorCode.FAILED
                self.write_ret(status)
                logging.error("[UWEB] terminal %s set too many event periods", tid)
            else:
                start_time = data["start_time"]
                end_time = data["end_time"]
                week = data["week"]
                self.db.execute("INSERT INTO T_ALERT_SETTING"
                                "  VALUES(NULL, %s, %s, %s, %s)",
                                tid, start_time, end_time, week)
                logging.info("[UWEB] terminal add event period success: %s", data)
                self.write_ret(status)
        except Exception as e:
            logging.exception("[UWEB] tid:%s insert event period. Exception:%s", 
                              tid, e.args)
            status = ErrorCode.FAILED
            self.write_ret(status)

    @authenticated
    @tornado.web.removeslash
    def delete(self):
        status = ErrorCode.SUCCESS
        try:
            tid = self.get_argument("tid")
            _id = self.get_argument("id")
            self.db.execute("DELETE FROM T_ALERT_SETTING"
                            "  WHERE tid=%s AND id=%s", 
                            tid, _id)
            logging.info("[UWEB] terminal delete event period success: tid is %s, id is %s", 
                         tid, _id)
            self.write_ret(status)
        except Exception as e:
            status = ErrorCode.FAILED
            logging.exception("[UWEB] terminal delete event period failed: tid:%s, id:%s. Exception:%s", 
                              tid, _id, e.args)
            self.write_ret(status)
