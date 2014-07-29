# -*- coding: utf-8 -*-

import logging
import datetime
import time
import hashlib
from os import SEEK_SET
import xlwt
from cStringIO import StringIO
from decimal import Decimal

from tornado.escape import json_decode, json_encode
import tornado.web

from utils.dotdict import DotDict
from utils.misc import DUMMY_IDS, str_to_list, start_end_of_year, start_end_of_month, start_end_of_day, start_end_of_quarter, days_of_month, get_date_from_utc
from utils.dotdict import DotDict
from helpers.queryhelper import QueryHelper
from helpers.lbmphelper import get_distance
from helpers.confhelper import ConfHelper
from codes.errorcode import ErrorCode
from constants import UWEB, EXCEL
from base import BaseHandler, authenticated

class MileageSingleHandler(BaseHandler):

    KEY_TEMPLATE = "mileage_single_statistic_%s_%s"

    @authenticated
    @tornado.web.removeslash
    def post(self):
        """Provide statistics about terminal.
        """
        status = ErrorCode.SUCCESS
        try:
            data = DotDict(json_decode(self.request.body))
            logging.info("[UWEB] Single statistic request: %s, uid: %s, tid: %s", 
                         data, self.current_user.uid, self.current_user.tid)
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            self.write_ret(status)
            return

        try:
            page_size = UWEB.LIMIT.PAGE_SIZE_STATISTICS
            page_number = int(data.pagenum)
            page_count = int(data.pagecnt)
            tid = data.tid
           
            res = []
            graphics = []
            counts = []
            label = u''
           
            dis_sum = Decimal() 
            
            current_time = int(time.time()) 

            statistics_type = data.statistics_type
            if statistics_type == UWEB.STATISTICS_TYPE.YEAR:
                label = data.year + u'年' 
                start_time, end_time = start_end_of_year(year=data.year)
                for month in range(1,12+1):
                    start_time_, end_time_ = start_end_of_month(year=data.year, month=str(month))
                    if start_time_ > current_time:
                        break

                    re = {} 
                    re['name'] = str(month)
                    distance = Decimal() 

                    mileage_log = self.db.get("SELECT SUM(distance) AS distance FROM T_MILEAGE_LOG" 
                                              "  WHERE tid = %s"
                                              "  AND (timestamp BETWEEN %s AND %s)",
                                              tid, start_time_, end_time_)
                    if mileage_log and mileage_log['distance']:
                        distance = '%0.1f' % (Decimal(mileage_log['distance'])/1000,)      
                    else: 
                        distance = 0
                    graphics.append(float(distance))
                    dis_sum += Decimal(distance)

                    re['mileage'] = float(distance)
                    res.append(re)
                counts = [float(dis_sum),]


            elif statistics_type == UWEB.STATISTICS_TYPE.MONTH:
                label = data.year + u'年' + data.month + u'月'
                start_time, end_time = start_end_of_month(year=data.year, month=data.month)
                days = days_of_month(year=data.year, month=data.month)

                distance = Decimal() 

                for day in range(1, days+1):
                    start_time_, end_time_ = start_end_of_day(year=data.year, month=data.month, day=str(day))
                    if start_time_ > current_time:
                        break

                    re = {} 
                    re['name'] = str(day)
                    distance = Decimal() 

                    mileage_log = self.db.get("SELECT distance FROM T_MILEAGE_LOG" 
                                              "  WHERE tid = %s"
                                              "  AND timestamp = %s",
                                              tid, end_time_)

                    distance = mileage_log['distance'] if mileage_log else 0

                    # meter --> km
                    distance = '%0.1f' % (Decimal(distance)/1000,)      

                    graphics.append(float(distance))
                    dis_sum += Decimal(distance)
                    re['mileage'] = float(distance)
                    res.append(re)

                counts = [float(dis_sum),]

            else:
                logging.error("[UWEB] Error statistics type: %s", statistics_type)
            
            
            if page_count == -1:
                items_count = len(res) 
                d, m = divmod(items_count, page_size) 
                page_count = (d + 1) if m else d

      
            # store resutl in redis
            m = hashlib.md5()
            m.update(self.request.body)
            hash_ = m.hexdigest()
            mem_key = self.KEY_TEMPLATE % (self.current_user.uid, hash_)
            
            self.redis.setvalue(mem_key, (res, counts, label, statistics_type), time=UWEB.STATISTIC_INTERVAL)

            res= res[page_number*page_size:(page_number+1)*page_size]

            self.write_ret(status, 
                           dict_=dict(res=res, 
                                      counts=counts,
                                      graphics=graphics,
                                      pagecnt=page_count,
                                      hash_=hash_)) 
        except Exception as e:
            logging.exception("[UWEB] uid:%s, tid:%s statistic failed. Exception: %s",
                              self.current_user.uid, self.current_user.tid, e.args)
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)
