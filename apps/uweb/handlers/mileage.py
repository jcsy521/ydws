# -*- coding: utf-8 -*-

import logging
import datetime
import time

from tornado.escape import json_decode, json_encode
import tornado.web

from utils.misc import days_of_month, str_to_list 
from utils.dotdict import DotDict
from helpers.queryhelper import QueryHelper
from helpers.lbmphelper import get_distance
from codes.errorcode import ErrorCode
from constants import UWEB
from base import BaseHandler, authenticated


class MileageHandler(BaseHandler):
    """Mileage report: distance of per day"""

    @authenticated
    @tornado.web.removeslash
    def post(self):
        """
        """
        status = ErrorCode.SUCCESS
        try:
            data = DotDict(json_decode(self.request.body))
            page_size = UWEB.LIMIT.PAGE_SIZE
            page_number = int(data.pagenum)
            page_count = int(data.pagecnt)
            start_time= data.start_time
            end_time = data.end_time
            tids = str_to_list(data.tids)
            logging.info("[UWEB] mileage request: %s, cid: %s, oid: %s", 
                         data, self.current_user.cid, self.current_user.oid)
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            self.write_ret(status)
            return

        try:
            # the interval between start_time and end_time is one week

            if self.current_user.cid != UWEB.DUMMY_CID: # no checks for  enterprise
                pass
            elif (int(end_time) - int(start_time)) > UWEB.QUERY_INTERVAL:
                self.write_ret(ErrorCode.QUERY_INTERVAL_EXCESS)
                return

            if page_count == -1:
                count = len(tids)
                d, m = divmod(count, page_size)
                page_count = (d + 1) if m else d
            tids = tids[(page_number * page_size):((page_number+1) * page_size)]
            reports = []
            for tid in tids:
                distance = 0
                points = self.db.query("SELECT longitude, latitude FROM T_LOCATION"
                                       "  WHERE tid = %s"
                                       "    AND (timestamp BETWEEN %s AND %s)"
                                       "    AND type = 0"
                                       "  ORDER BY timestamp asc",
                                       tid, start_time, end_time)
                for i in range(len(points)-1):
                    if points[i].longitude and points[i].latitude and \
                       points[i+1].longitude and points[i+1].latitude:
                        distance += get_distance(points[i].longitude, points[i].latitude,
                                                 points[i+1].longitude, points[i+1].latitude) 
                # meter --> km
                distance = '%0.1f' % (distance/1000,)
                alias = QueryHelper.get_alias_by_tid(tid, self.redis, self.db)
                dct = DotDict(tid=tid,
                              alias=alias,
                              distance=distance)
                reports.append(dct)
            self.write_ret(status,
                           dict_=DotDict(res=reports,
                                         pagecnt=page_count))
        except Exception as e:
            logging.exception("[UWEB] cid:%s, oid:%s get mileage report failed. Exception: %s",
                              self.current_user.cid, self.current_user.oid, e.args)
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)
