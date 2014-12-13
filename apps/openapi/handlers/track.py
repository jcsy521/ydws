# -*- coding: utf-8 -*-

import time
import os
import logging

import tornado.web
from tornado.escape import json_encode, json_decode

from utils.dotdict import DotDict
from codes.openapi_errorcode import ErrorCode
from constants import UWEB, OPENAPI
from helpers.queryhelper import QueryHelper 
from helpers.openapihelper import OpenapiHelper 
from helpers.lbmphelper import get_locations_with_clatlon
from utils.track import get_track

from base import BaseHandler

class TrackHandler(BaseHandler):

    @tornado.web.removeslash
    def post(self):
        """Get locatons in same period.
        location type:　gps
        """
        status = ErrorCode.SUCCESS
        res = []
        try:
            data = DotDict(json_decode(self.request.body))
            mobile = data.mobile
            start_time = data.start_time
            end_time = data.end_time
            token = data.token
            logging.info("[TRACK] Request, data:%s", data)
        except Exception as e:
            logging.exception("[TRACK] Invalid data format, body: %s, tid: %s.",
                              self.request.body, tid)
            status = ErrorCode.DATA_FORMAT_INVALID
            self.write_ret(status)
            return

        try:
            if (not token) or not OpenapiHelper.check_token(token, self.redis):
                status = ErrorCode.TOKEN_EXPIRED
                logging.info("[TRACK] Failed. Message: %s.",
                             ErrorCode.ERROR_MESSAGE[status])
                self.write_ret(status)
                return
            else:
                terminal = self.db.get("SELECT tid FROM T_TERMINAL_INFO"
                                       "  WHERE mobile = %s"
                                       "  AND service_status = %s",
                                       mobile, UWEB.SERVICE_STATUS.ON)
                if not terminal:
                    status = ErrorCode.MOBILE_NOT_EXISTED
                    logging.info("[TRACK] Failed. Message: %s.",
                                 ErrorCode.ERROR_MESSAGE[status])
                    self.write_ret(status)
                else: 
                    tid = terminal.tid
                    track = get_track(self.db, self.redis, tid, start_time, end_time, cellid=False)
                    for t in track:
                        d = dict(lon=t.get('longitude', 0),
                                   lat=t.get('latitude', 0),
                                   clon=t.get('clongitude', 0),
                                   clat=t.get('clatitude', 0),
                                   timestamp=t.get('timestamp',0),
                                   name=t.get('name',''))
                        res.append(d)
                    
            
            self.write_ret(status,
                           dict_=dict(res=res))

        except Exception as e:
            logging.exception("[MILEAGE] mobile: %s. Exception: %s",
                              mobile, e.args)
            status = ErrorCode.FAILED
            self.write_ret(status)
