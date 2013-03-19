# -*- coding: utf-8 -*-

import logging
import datetime
import time
from dateutil.relativedelta import relativedelta

from tornado.escape import json_decode, json_encode
import tornado.web

from helpers.seqgenerator import SeqGenerator
from helpers.queryhelper import QueryHelper 
from helpers.confhelper import ConfHelper
from utils.misc import DUMMY_IDS, get_today_last_month, str_to_list,\
                       get_terminal_info_key
from utils.dotdict import DotDict
from codes.errorcode import ErrorCode
from constants import UWEB, EVENTER 
from base import BaseHandler, authenticated

class EventHandler(BaseHandler):
    """Offer various events for web request."""

    @authenticated
    @tornado.web.removeslash
    def get(self):
        """Jump to event.html, provide alias """ 
        tid = self.get_argument('tid',None) 
        # check tid whether exist in request and update current_user
        self.check_tid(tid)
          
        terminal = self.db.get("SELECT id FROM T_TERMINAL_INFO"
                               "  WHERE tid = %s"
                               "    AND service_status = %s",
                               self.current_user.tid,
                               UWEB.SERVICE_STATUS.ON)
        if not terminal:
            status = ErrorCode.LOGIN_AGAIN
            logging.error("The terminal with tid: %s does not exist, redirect to login.html", self.current_user.tid)
            self.render("login.html",
                        map_type=ConfHelper.LBMP_CONF.map_type,
                        alias='')
            return
        
        alias = QueryHelper.get_alias_by_tid(self.current_user.tid, self.redis, self.db)
        self.render("event.html",
                    map_type=ConfHelper.LBMP_CONF.map_type,
                    alias=alias)

    @authenticated
    @tornado.web.removeslash
    def post(self):
        """Retrive various event.
        """
        status = ErrorCode.SUCCESS
        try:
            data = DotDict(json_decode(self.request.body))
            tid = data.get('tid', None) 
            tids = data.get('tids', None)
            # check tid whether exist in request and update current_user
            self.check_tid(tid)
            logging.info("[UWEB] event request: %s, uid: %s, tid: %s, tids: %s", 
                         data, self.current_user.uid, self.current_user.tid, tids)
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            self.write_ret(status)
            return

        try:
            terminal = self.db.get("SELECT id FROM T_TERMINAL_INFO"
                                   "  WHERE tid = %s"
                                   "    AND service_status = %s",
                                   self.current_user.tid,
                                   UWEB.SERVICE_STATUS.ON)
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
            tids = str_to_list(tids)
            tids = tids if tids else [self.current_user.tid, ]
            tids = [str(tid) for tid in tids]
            # the interval between start_time and end_time is one week
            if (int(end_time) - int(start_time)) > UWEB.QUERY_INTERVAL:
                self.write_ret(ErrorCode.QUERY_INTERVAL_EXCESS)
                return

            if category == -1:
                # we need return the event count to GUI at first time query
                if page_count == -1:
                    sql = ("SELECT COUNT(*) as count FROM V_EVENT" +\
                          "  WHERE tid IN %s" +\
                          "    AND (timestamp BETWEEN %s AND %s)")\
                          % (tuple(tids + DUMMY_IDS), start_time, end_time)
                    res = self.db.get(sql)
                    event_count = res.count
                    d, m = divmod(event_count, page_size)
                    page_count = (d + 1) if m else d

                sql = ("SELECT tid, latitude, longitude, clatitude, clongitude," 
                      "  timestamp, name, type, speed, degree,"
                      "  category, pbat, terminal_type, fobid"  
                      "  FROM V_EVENT"
                      "  WHERE tid IN %s"
                      "    AND (timestamp BETWEEN %s AND %s)"
                      "    AND category != 5"
                      "  ORDER BY timestamp DESC"
                      "  LIMIT %s, %s") %\
                      (tuple(tids + DUMMY_IDS), start_time, end_time,
                       page_number * page_size, page_size)
                events = self.db.query(sql)
            else: 
                if page_count == -1:
                    sql = ("SELECT COUNT(*) as count FROM V_EVENT"
                           "  WHERE tid IN %s"
                           "    AND (timestamp BETWEEN %s AND %s)"
                           "    AND category = %s") %\
                           (tuple(tids + DUMMY_IDS), start_time, end_time, category)
                    res = self.db.get(sql)
                    event_count = res.count
                    d, m = divmod(event_count, page_size)
                    page_count = (d + 1) if m else d

                sql = ("SELECT tid, latitude, longitude, clatitude, clongitude," 
                       "  timestamp, name, type, speed, degree,"
                       "  category, pbat, terminal_type, fobid"  
                       "  FROM V_EVENT"
                       "  WHERE tid IN %s"
                       "    AND (timestamp BETWEEN %s AND %s)"
                       "    AND category = %s"
                       "  ORDER BY timestamp DESC"
                       "  LIMIT %s, %s") %\
                       (tuple(tids + DUMMY_IDS), start_time, end_time, category, page_number * page_size, page_size)

                events = self.db.query(sql)

            alias_dict = {}
            for tid in tids:
                terminal_info_key = get_terminal_info_key(tid)
                terminal_info = self.redis.getvalue(terminal_info_key)
                alias_dict[tid] = terminal_info['alias'] if terminal_info['alias'] else terminal_info['mobile']
            # change the type form decimal to float.
            for event in events:
                event['alias'] = alias_dict[event['tid']] 
                event['pbat'] = event['pbat'] if event['pbat'] is not None else 0
                event['fobid'] = event['fobid'] if event['fobid'] is not None else u''
                event['name'] = event['name'] if event['name'] is not None else u''
                event['degree'] = float(event['degree'])
                event['speed'] = float(event['speed'])
                event['comment'] = ''
                if event['category'] == EVENTER.CATEGORY.POWERLOW:
                    if event['terminal_type'] == '1':
                        if int(event['pbat']) == 100:
                            event['comment'] = ErrorCode.ERROR_MESSAGE[ErrorCode.TRACKER_POWER_FULL] 
                        elif int(event['pbat']) <= 5:
                            event['comment'] = ErrorCode.ERROR_MESSAGE[ErrorCode.TRACKER_POWER_OFF] 
                        else:
                            event['comment'] = (ErrorCode.ERROR_MESSAGE[ErrorCode.TRACKER_POWER_LOW]) % event['pbat']
                    else:
                        event['comment'] = ErrorCode.ERROR_MESSAGE[ErrorCode.FOB_POWER_LOW] % event['fobid']
                
            self.write_ret(status,
                           dict_=DotDict(res=events,
                                         pagecnt=page_count))
        except Exception as e:
            logging.exception("[UWEB] uid:%s, tid:%s get alarm info failed. Exception: %s",
                              self.current_user.uid, self.current_user.tid, e.args)
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)


