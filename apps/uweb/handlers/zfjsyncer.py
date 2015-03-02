# -*- coding: utf-8 -*-

"""The module is designed for 中山执法局.

When Open API is release, it becomes unused.

#NOTE： deprecated.
"""

import logging
import time

import tornado.web

from helpers.queryhelper import QueryHelper
from helpers.lbmphelper import get_locations_with_clatlon
from base import BaseHandler

class ZFJSyncerHandler(BaseHandler):

    @tornado.web.removeslash
    def post(self):
        res = list()
        try:
            corp_id = 13726103889   #开发区执法局
            begin_time = self.redis.getvalue('last_time')
            end_time = time.time()
            self.redis.setvalue('last_time', end_time)
            if (end_time - begin_time) < 14*60: # 14 分钟
                logging.info("[UWEB] ZFJ request too frequency,"
                             " skip it, begin time:%s, end time:%s", 
                             begin_time, end_time)
                self.write({'res':res})
                return

            logging.info("[UWEB] ZFJ request, begin time:%s, end time:%s", 
                         begin_time, end_time)
            if begin_time:
                terminals = QueryHelper.get_terminals_by_cid(corp_id,self.db)
                for terminal in terminals:
                    mobile = terminal['mobile']
                    tid = terminal['tid']
                    positions = self.db.query("SELECT id, latitude, longitude,"
                                              "  clatitude, clongitude, timestamp"
                                              "  FROM T_LOCATION"
                                              "  WHERE tid=%s" 
                                              "  AND timestamp BETWEEN %s AND %s"
                                              "  AND latitude != 0"
                                              "  AND longitude != 0"
                                              "  ORDER BY timestamp",
                                              tid, begin_time , end_time)

                    _start_time = time.time()
                    positions = get_locations_with_clatlon(positions, self.db) 
                    _now_time = time.time()
                    if _now_time - _start_time > 3: # 3 seconds
                        logging.info("[UWEB] Track offset used time: %s s, tid: %s, cid: %s",
                                     _now_time - _start_time, tid, corp_id)
                    res.append({'mobile':mobile, 'positions':positions})
            self.write({'res':res})

        except Exception as e:
            logging.exception("[UWEB] zfjsyncer: get location failed. Exception: %s", 
                              e.args) 
