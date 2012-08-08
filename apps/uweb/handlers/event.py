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
        """Jump to event.html, provide tid, alias """ 
        terminal = QueryHelper.get_terminal_by_tid(self.current_user.tid, self.db)
        self.render("event.html",
                    tid=self.current_user.tid,
                    alias=terminal.alias if terminal.alias else self.current_user.sim)

    @authenticated
    @tornado.web.removeslash
    def post(self):
        """Retrive various event.
        """
        try:
            page_size = UWEB.LIMIT.PAGE_SIZE

            data = DotDict(json_decode(self.request.body))
            event_type = int(data.event_type)
            page_number = int(data.pagenum)
            page_count = int(data.pagecnt)
            start_time = data.start_time
            end_time = data.end_time
            tid = data.tid
            # the interval between start_time and end_time is one week
            if (int(end_time) - int(start_time)) > UWEB.QUERY_INTERVAL:
                self.write_ret(ErrorCode.QUERY_INTERVAL_EXCESS)
                return

            if event_type == -1:
                # we need return the event count to GUI at first time query
                if page_count == -1:
                    res = self.db.get("SELECT COUNT(*) as count FROM V_EVENT"
                                      "  WHERE tid = %s"
                                      "    AND (timestamp BETWEEN %s AND %s)",
                                      tid, start_time, end_time)
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
                                       tid, start_time, end_time,
                                       page_number * page_size, page_size)
            else: 
                if page_count == -1:
                    res = self.db.get("SELECT COUNT(*) as count FROM V_EVENT"
                                      "  WHERE tid = %s"
                                      "    AND (timestamp BETWEEN %s AND %s)"
                                      "    AND category = %s",
                                      tid, start_time, end_time, event_type)
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
                                       tid, start_time, end_time, event_type,
                                       page_number * page_size, page_size)

            # change the type form decimal to float.
            for event in events:
                event['degree'] = float(event['degree'])
                
            self.write_ret(ErrorCode.SUCCESS,
                          dict_=DotDict(events=events,
                                        pagecnt=page_count))
        except Exception as e:
            logging.exception("Get track failed. Exception: %s", e.args)
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)
