# -*- coding: utf-8 -*-

import logging
import datetime
import time
from dateutil.relativedelta import relativedelta

from tornado.escape import json_decode, json_encode
import tornado.web

from helpers.seqgenerator import SeqGenerator
from helpers.queryhelper import QueryHelper 
from utils.misc import DUMMY_IDS, get_today_last_month
from utils.dotdict import DotDict
from codes.errorcode import ErrorCode
from constants import UWEB 
from base import BaseHandler, authenticated

class EventHandler(BaseHandler):
    """Offer various events for web request."""

    @authenticated
    @tornado.web.removeslash
    def get(self):
        """Jump to event.html, provide alias """ 
        terminal = QueryHelper.get_terminal_by_tid(self.current_user.tid, self.db)
        if not terminal:
            status = ErrorCode.LOGIN_AGAIN
            logging.error("The terminal with tid: %s does not exist, redirect to login.html", self.current_user.tid)
            self.render("event.html",
                        alias='')
            return
        
        alias = QueryHelper.get_alias_by_tid(self.current_user.tid, self.redis, self.db)
        self.render("event.html",
                    alias=alias)

    @authenticated
    @tornado.web.removeslash
    def post(self):
        """Retrive various event.
        """
        status = ErrorCode.SUCCESS
        try:
            data = DotDict(json_decode(self.request.body))
            logging.info("[UWEB] event request: %s, uid: %s, tid: %s", 
                         data, self.current_user.uid, self.current_user.tid)
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            self.write_ret(status)
            return

        try:
            terminal = QueryHelper.get_terminal_by_tid(self.current_user.tid, self.db)
            if not terminal:
                status = ErrorCode.LOGIN_AGAIN
                logging.error("The terminal with tid: %s does not exist, redirect to login.html", self.current_user.tid)
                self.write_ret(status)
                return

            page_size = UWEB.LIMIT.PAGE_SIZE
            category = int(data.category)
            page_number = int(data.pagenum)
            page_count = int(data.pagecnt)
            start_time = data.start_time
            end_time = data.end_time
            # the interval between start_time and end_time is one week
            if (int(end_time) - int(start_time)) > UWEB.QUERY_INTERVAL:
                self.write_ret(ErrorCode.EVENT_QUERY_INTERVAL_EXCESS)
                return

            if category == -1:
                # we need return the event count to GUI at first time query
                if page_count == -1:
                    res = self.db.get("SELECT COUNT(*) as count FROM V_EVENT"
                                      "  WHERE tid = %s"
                                      "    AND (timestamp BETWEEN %s AND %s)",
                                      self.current_user.tid, start_time, end_time)
                    event_count = res.count
                    d, m = divmod(event_count, page_size)
                    page_count = (d + 1) if m else d

                events = self.db.query("SELECT latitude, longitude, clatitude, clongitude," 
                                       "  timestamp, name, type, speed, degree, category"  
                                       "  FROM V_EVENT"
                                       "  WHERE tid = %s"
                                       "    AND (timestamp BETWEEN %s AND %s)"
                                       "  ORDER BY timestamp DESC"
                                       "  LIMIT %s, %s",
                                       self.current_user.tid, start_time, end_time,
                                       page_number * page_size, page_size)
            else: 
                if page_count == -1:
                    res = self.db.get("SELECT COUNT(*) as count FROM V_EVENT"
                                      "  WHERE tid = %s"
                                      "    AND (timestamp BETWEEN %s AND %s)"
                                      "    AND category = %s",
                                      self.current_user.tid, start_time, end_time, category)
                    event_count = res.count
                    d, m = divmod(event_count, page_size)
                    page_count = (d + 1) if m else d

                events = self.db.query("SELECT latitude, longitude, clatitude, clongitude," 
                                       "  timestamp, name, type, speed, degree, category"  
                                       "  FROM V_EVENT"
                                       "  WHERE tid = %s"
                                       "    AND (timestamp BETWEEN %s AND %s)"
                                       "    AND category = %s"
                                       "  ORDER BY timestamp DESC"
                                       "  LIMIT %s, %s",
                                       self.current_user.tid, start_time, end_time, category,
                                       page_number * page_size, page_size)

            # change the type form decimal to float.
            for event in events:
                event['degree'] = float(event['degree'])
                event['speed'] = float(event['speed'])
                
            self.write_ret(status,
                           dict_=DotDict(events=events,
                                         pagecnt=page_count))
        except Exception as e:
            logging.exception("[UWEB] uid:%s, tid:%s get alarm info failed. Exception: %s",
                              self.current_user.uid, self.current_user.tid, e.args)
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)
