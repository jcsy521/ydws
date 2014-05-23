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


class MileageJuniorHandler(BaseHandler):
    """Junior Mileage."""

    KEY_TEMPLATE = "mileage_statistic_%s_%s"

    @authenticated
    @tornado.web.removeslash
    @tornado.web.asynchronous
    def post(self):
        """ Provide some statistics about terminals.
        """
      
        status = ErrorCode.SUCCESS
        #NOTE: check data format
        try:
            data = DotDict(json_decode(self.request.body))
            page_size = UWEB.LIMIT.PAGE_SIZE
            page_number = int(data.pagenum)
            page_count = int(data.pagecnt)
            start_time= data.start_time
            end_time = data.end_time
            query_type = data.query_type
            tids = str_to_list(data.tids)
            logging.info("[UWEB] mileage request: %s, cid: %s, oid: %s", 
                         data, self.current_user.cid, self.current_user.oid)
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            logging.exception("[UWEB] Invalid data format. Exception: %s",
                              e.args)
            self.write_ret(status)
            self.finish()
            return

        #NOTE: prepare  
        try:
            # the interval between start_time and end_time is one week
            if self.current_user.cid != UWEB.DUMMY_CID: # no checks for enterprise
                pass
            elif (int(end_time) - int(start_time)) > UWEB.QUERY_INTERVAL:
                self.write_ret(ErrorCode.QUERY_INTERVAL_EXCESS)
                self.finish()
                return

            statistic_mode = 'single' 
            if not tids: # all terminals
                statistic_mode = 'all' 
                terminals = QueryHelper.get_terminals_by_cid(self.current_user.cid, self.db)
                tids = [terminal.tid for terminal in terminals]
        except Exception as e:
            logging.exception("[UWEB] cid:%s, oid:%s get mileage report failed. Exception: %s",
                              self.current_user.cid, self.current_user.oid, e.args)
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)
            self.finish()
            return

        def _on_finish(db):
            self.db = db
            page_count = int(data.pagecnt)
            if statistic_mode == 'all': # all
                if page_count == -1:
                    count = len(tids)
                    d, m = divmod(count, page_size)
                    page_count = (d + 1) if m else d

                reports = []
                interval = [start_time, end_time]
                for item, tid in enumerate(tids):
                    seq = item + 1
                    dis_sum = Decimal()  

                    start_date = get_date_from_utc(start_time)
                    end_date = get_date_from_utc(end_time)
                    start_day = datetime.datetime.fromtimestamp(start_time)
                    end_day = datetime.datetime.fromtimestamp(end_time)
                    # get how many days the end_time and start_time cover
                    days = abs(end_day-start_day).days+1

                    for item in range(days):
                        distance = Decimal()
                        timestamp = start_time+1*60*60*24*(item)
                        date = get_date_from_utc(timestamp)
                        year, month, day = date.year, date.month, date.day
                        start_time_, end_time_ = start_end_of_day(year=year, month=month, day=day)

                        mileage_log = self.db.get("SELECT distance FROM T_MILEAGE_LOG" 
                                                  "  WHERE tid = %s"
                                                  "  AND timestamp = %s",
                                                  tid, end_time_)
                        distance = mileage_log['distance'] if mileage_log else 0
                         
                        # meter --> km
                        distance = '%0.1f' % (distance/1000,)
                        dis_sum += Decimal(distance)

                    alias = QueryHelper.get_alias_by_tid(tid, self.redis, self.db)
                    dct = dict(seq=seq,
                               alias=alias,
                               distance=float(dis_sum))
                    reports.append(dct)

                # orgnize and store the data to be downloaded 
                m = hashlib.md5()
                m.update(self.request.body)
                hash_ = m.hexdigest()
                mem_key = self.KEY_TEMPLATE % (self.current_user.uid, hash_)
                
                self.redis.setvalue(mem_key, (statistic_mode, reports, 0), time=UWEB.STATISTIC_INTERVAL)

                reports= reports[(page_number * page_size):((page_number+1) * page_size)]
                self.write_ret(status,
                               dict_=DotDict(res=reports,
                                             pagecnt=page_count,
                                             hash_=hash_))
            else: # single
                tid = tids[0]
                delta = end_time - start_time # end_time must bigger than start_time
                d, m = divmod(delta, 60*60*24) 
                start_date = get_date_from_utc(start_time)
                end_date = get_date_from_utc(end_time)
                start_day = datetime.datetime.fromtimestamp(start_time)
                end_day = datetime.datetime.fromtimestamp(end_time)
                # get how many days the end_time and start_time cover
                days = abs(end_day-start_day).days+1
                #if days == 0: 
                #    if start_date.day  == end_date.day:   
                #        days = 1
                #    else: 
                #        days = 2
                #else: 
                #    days = days+1 if m else days
                #    if end_day.hour*60*60 + end_day.minute*60 + end_day.second <  start_day.hour*60*60 + start_day.minute*60 + start_day.second:                   
                #        days = days+1 
  
                res = []
                graphics = [] 
                counts = []
                dis_sum = Decimal() 
                current_time = int(time.time()) 

                for item in range(days):
                    timestamp = start_time+1*60*60*24*(item)
                    date = get_date_from_utc(timestamp)
                    year, month, day = date.year, date.month, date.day
                    start_time_, end_time_ = start_end_of_day(year=year, month=month, day=day)

                    re = {} 
                    re['alias'] = '-'.join([str(year),str(month),str(day)]) 

                    mileage_log = self.db.get("SELECT distance FROM T_MILEAGE_LOG" 
                                              "  WHERE tid = %s"
                                              "  AND timestamp = %s",
                                              tid, end_time_)
                    distance = mileage_log['distance'] if mileage_log else 0

                    # meter --> km
                    distance = '%0.1f' % (distance/1000,)      

                        
                    graphics.append(float(distance))
                    dis_sum += Decimal(distance)

                    re['distance'] = distance 
                    re['seq'] = item+1 
                    res.append(re)

                counts = [float(dis_sum),]

                if page_count == -1:
                    items_count = len(res) 
                    d, m = divmod(items_count, page_size) 
                    page_count = (d + 1) if m else d
    
                # store resutl in redis
                m = hashlib.md5()
                m.update(self.request.body)
                hash_ = m.hexdigest()
                mem_key = self.KEY_TEMPLATE % (self.current_user.uid, hash_)
                
                self.redis.setvalue(mem_key, (statistic_mode, res, counts,), time=UWEB.STATISTIC_INTERVAL)
    
                res= res[page_number*page_size:(page_number+1)*page_size]
                self.write_ret(status, 
                               dict_=dict(res=res, 
                                          counts=counts,
                                          graphics=graphics,
                                          pagecnt=page_count,
                                          hash_=hash_)) 
            self.finish()
        self.queue.put((10, _on_finish))