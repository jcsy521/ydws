# -*- coding: utf-8 -*-

import logging
import time
import re

import tornado.web

from codes.errorcode import ErrorCode
from helpers.queryhelper import QueryHelper
from base import BaseHandler, authenticated


class ZFJSyncerHandler(BaseHandler):

    @tornado.web.removeslash
    def post(self):
        res = list()
        try:
            corp_id = 13928191116   #东升执法局
            ip = self.request.remote_ip
            ips = re.compile('192.168.1.*')
            if ips.match(ip):
                begin_time = self.redis.getvalue('last_time')
                end_time = time.time()
                if begin_time:
                    terminals = QueryHelper.get_terminals_by_cid(corp_id,self.db)
                    for terminal in terminals:
                        mobile = terminal['mobile']
                        tid = terminal['tid']
                        positions = self.db.query("SELECT latitude, longitude, timestamp FROM T_LOCATION WHERE tid=%s AND timestamp BETWEEN %s AND %s ORDER BY timestamp", tid, begin_time , end_time)
                        res.append({'mobile':mobile, 'positions':positions})
                self.redis.setvalue('last_time', end_time)
                self.write({'res':res})
            else:
                self.write({'res':res})
                logging.error("Error: wrong ip.")
        except Exception as e:
            self.write({'res':res})
            logging.exception("[UWEB] zfjsyncer: get location failed. Exception: %s", e.args) 

