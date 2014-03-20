# -*- coding: utf-8 -*-

import logging

from tornado.escape import json_decode, json_encode
import tornado.web

from helpers.queryhelper import QueryHelper 
from helpers.confhelper import ConfHelper
from utils.misc import DUMMY_IDS_STR, DUMMY_IDS, safe_unicode, str_to_list, get_terminal_info_key
from utils.dotdict import DotDict
from codes.errorcode import ErrorCode
from constants import UWEB, EVENTER 
from base import BaseHandler, authenticated

class AttendanceHandler(BaseHandler):
    """Offer attendance log."""

    @authenticated
    @tornado.web.removeslash
    def get(self):
        """Jump to attendance.html, provide alias """ 
        mobile = self.get_argument('mobile', None) 
        terminal = self.db.get("SELECT id, tid FROM T_TERMINAL_INFO"
                               "  WHERE mobile = %s"
                               "    AND service_status = %s",
                               mobile,
                               UWEB.SERVICE_STATUS.ON)
        if not terminal:
            status = ErrorCode.LOGIN_AGAIN
            logging.error("The terminal with mobile: %s does not exist, redirect to login.html", self.current_user.tid)
            self.render("login.html",
                        map_type=ConfHelper.LBMP_CONF.map_type,
                        alias='')
            return
        
        alias = QueryHelper.get_alias_by_tid(terminal['tid'], self.redis, self.db)
        self.render("attendance.html",
                    map_type=ConfHelper.LBMP_CONF.map_type,
                    alias=alias)

    @authenticated
    @tornado.web.removeslash
    def post(self):
        """Retrive various attendance.
        """
        status = ErrorCode.SUCCESS
        try:
            data = DotDict(json_decode(self.request.body))

            mobile = data.get('mobile', None)
            mobiles = str_to_list(mobile)

            if not mobiles:
                terminals = self.db.query("SELECT tmobile FROM V_TERMINAL"
                                          "  where cid = %s", 
                                          self.current_user.cid)
                mobiles = [str(terminal['tmobile']) for terminal in terminals]
            logging.info("[UWEB] attendance request: %s, cid: %s", 
                         data, self.current_user.cid)
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            logging.exception("[UWEB] Invalid data format. Exception: %s",
                              e.args)
            self.write_ret(status)
            return

        try:
            page_size = int(data.get('pagesize', UWEB.LIMIT.PAGE_SIZE))
            page_number = int(data.pagenum)
            page_count = int(data.pagecnt)
            start_time = data.start_time
            end_time = data.end_time

            # we need return the event count to GUI at first time query
            if page_count == -1:
                sql = ("SELECT COUNT(*) as count FROM V_ATTENDANCE" 
                       "  WHERE mobile IN %s " 
                       "    AND (timestamp BETWEEN %s AND %s)") 

                sql = sql % (tuple(mobiles + DUMMY_IDS_STR), start_time, end_time)
                res = self.db.get(sql)
                event_count = res.count
                d, m = divmod(event_count, page_size)
                page_count = (d + 1) if m else d

            sql = ("SELECT tid, mobile, clatitude, clongitude," 
                   "  timestamp, name, type, speed, degree,"
                   "  locate_error"  
                   "  FROM V_ATTENDANCE"
                   "  WHERE mobile IN %s"
                   "    AND (timestamp BETWEEN %s AND %s)"
                   "  ORDER BY timestamp DESC"
                   "  LIMIT %s, %s") 
            sql = sql % (tuple(mobiles + DUMMY_IDS_STR), start_time, end_time, page_number * page_size, page_size)

            res = self.db.query(sql)
                
            # change the type form decimal to float.
            for r in res:
                r['alias'] = QueryHelper.get_alias_by_tid(r['tid'], self.redis, self.db)
                r['name'] = r['name'] if r['name'] is not None else u''
                r['degree'] = float(r['degree'])
                r['speed'] = float(r['speed'])
                r['comment'] = ''
                
            self.write_ret(status,
                           dict_=DotDict(res=res,
                                         pagecnt=page_count))
        except Exception as e:
            status = ErrorCode.SERVER_BUSY
            logging.exception("[UWEB] cid:%s get attendance info failed. Exception: %s",
                              self.current_user.cid, e.args)
            self.write_ret(status)
