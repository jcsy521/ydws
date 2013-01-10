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
from constants import UWEB, EVENTER 
from base import BaseHandler, authenticated

class StatisticHandler(BaseHandler):

    @authenticated
    @tornado.web.removeslash
    def post(self):
        """Provie some statistics about terminals.
        """
        status = ErrorCode.SUCCESS
        try:
            data = DotDict(json_decode(self.request.body))
            logging.info("[UWEB] statistic request: %s, uid: %s, tid: %s", 
                         data, self.current_user.uid, self.current_user.tid)
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            self.write_ret(status)
            return

        try:
            res = []
            page_size = UWEB.LIMIT.PAGE_SIZE
            page_number = int(data.pagenum)
            page_count = int(data.pagecnt)
            start_time = data.start_time
            end_time = data.end_time
            # the interval between start_time and end_time is one week
            if (int(end_time) - int(start_time)) > UWEB.QUERY_INTERVAL:
                self.write_ret(ErrorCode.QUERY_INTERVAL_EXCESS)
                return

            CATEGORY_DCT = DotDict(powerlow=EVENTER.CATEGORY.POWERLOW,
                                   illegashake=EVENTER.CATEGORY.ILLEGALSHAKE,
                                   illegalmove=EVENTER.CATEGORY.ILLEGALMOVE,
                                   sos=EVENTER.CATEGORY.EMERGENCY,
                                   heartbeat_lost=EVENTER.CATEGORY.HEARTBEAT_LOST)

            corp = self.db.get("SELECT cid, name, mobile FROM T_CORP WHERE cid = %s", self.current_user.cid)
            groups = self.db.query("SELECT id gid, name FROM T_GROUP WHERE corp_id = %s", self.current_user.cid)

            group_ids = [int(group.gid) for group in groups]

            terminals = self.db.query("SELECT tid, mobile FROM T_TERMINAL_INFO WHERE group_id IN %s",
                        tuple(group_ids+DUMMY_IDS))

            for terminal in terminals: 
                res_item = DotDict()
                res_item['tmobile'] = terminal.mobile
                tid = terminal.tid
                for key, category in CATEGORY_DCT.iteritems():
                     item = self.db.get("SELECT COUNT(*) as count FROM V_EVENT"
                                      "  WHERE tid = %s"
                                      "    AND (timestamp BETWEEN %s AND %s)"
                                      "    AND category = %s",
                                      tid, start_time, end_time, category)
                     res_item[key] = item.count
                res.append(res_item)

            if page_count == -1:
                items_count = len(res) 
                d, m = divmod(items_count, page_size) 
                page_count = (d + 1) if m else d
            
            res = res[page_number*page_size:(page_number+1)*page_size]
            self.write_ret(status, 
                           dict_=DotDict(res=res,
                                         pagecnt=page_count))
        except Exception as e:
            logging.exception("[UWEB] uid:%s, tid:%s statistic failed. Exception: %s",
                              self.current_user.uid, self.current_user.tid, e.args)
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)
