# -*- coding: utf-8 -*-

"""This module is designed for mileage of Open API.
"""

import datetime
import logging

import tornado.web
from tornado.escape import json_encode, json_decode

from utils.dotdict import DotDict
from codes.openapi_errorcode import ErrorCode
from constants import UWEB, OPENAPI
from helpers.queryhelper import QueryHelper 
from helpers.openapihelper import OpenapiHelper
from helpers.lbmphelper import get_locations_with_clatlon
from utils.misc import start_end_of_day, get_date_from_utc

from base import BaseHandler


class MileageHandler(BaseHandler):

    @tornado.web.removeslash
    def post(self):
        """Get mileage of a terminal.
        """
        status = ErrorCode.SUCCESS
        res = []
        try:
            data = DotDict(json_decode(self.request.body))
            mobile = data.mobile
            start_time = int(data.start_time)
            end_time = int(data.end_time)
            token = data.token
            logging.info("[MILEAGE] Request, data:%s", data)
        except Exception as e:
            status = ErrorCode.DATA_FORMAT_INVALID
            logging.exception("[MILEAGE] Invalid data format, body: %s, ",
                              self.request.body)
            self.write_ret(status)
            return

        try:
            status = self.basic_check(token, mobile)                             
            if status != ErrorCode.SUCCESS:
                self.write_ret(status)
                return

            terminal = QueryHelper.get_terminal_by_tmobile(mobile, self.db)
            tid = terminal.tid
            # end_time must bigger than start_time
            delta = end_time - start_time
            d, m = divmod(delta, 60 * 60 * 24)
            start_date = get_date_from_utc(start_time)
            end_date = get_date_from_utc(end_time)
            start_day = datetime.datetime.fromtimestamp(start_time)
            end_day = datetime.datetime.fromtimestamp(end_time)
            # get how many days the end_time and start_time cover
            days = abs(end_day - start_day).days + 1

            for item in range(days):
                timestamp = start_time + 1 * 60 * 60 * 24 * (item)
                date = get_date_from_utc(timestamp)
                year, month, day = date.year, date.month, date.day
                start_time_, end_time_ = start_end_of_day(
                    year=year, month=month, day=day)

                date = '-'.join([str(year), str(month), str(day)])

                mileage_log = self.db.get("SELECT distance FROM T_MILEAGE_LOG"
                                          "  WHERE tid = %s"
                                          "  AND timestamp = %s",
                                          tid, end_time_)
                mileage = mileage_log['distance'] if mileage_log else 0

                r = dict(date=date,
                         mileage=mileage)
                res.append(r)
                
            self.write_ret(status,
                           dict_=dict(res=res))

        except Exception as e:
            logging.exception("[MILEAGE] mobile: %s. Exception: %s",
                              mobile, e.args)
            status = ErrorCode.FAILED
            self.write_ret(status)
