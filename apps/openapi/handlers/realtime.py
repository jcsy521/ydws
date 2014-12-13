# -*- coding: utf-8 -*-

import time
import logging

import tornado.web
from tornado.escape import json_encode, json_decode

from utils.dotdict import DotDict
from codes.openapi_errorcode import ErrorCode
from helpers.lbmphelper import get_locations_with_clatlon
from constants import UWEB, OPENAPI
from helpers.queryhelper import QueryHelper 
from helpers.openapihelper import OpenapiHelper 

from base import BaseHandler

class RealtimeHandler(BaseHandler):

    @tornado.web.removeslash
    def post(self):
        """Get last location of a terminal.
        """
        status = ErrorCode.SUCCESS
        res = {}
        try:
            data = DotDict(json_decode(self.request.body))
            mobile = data.mobile
            timestamp = data.timestamp
            token = data.token
            logging.info("[REALTIME] Request, data:%s", data)
        except Exception as e:
            logging.exception("[REALTIME] Invalid data format, body: %s, mobile: %s.",
                              self.request.body, mobile)
            status = ErrorCode.DATA_FORMAT_ILLEGAL
            self.write_ret(status)
            return

        try:
            if not token or not OpenapiHelper.check_token(token, self.redis):
                status = ErrorCode.TOKEN_EXPIRED
                logging.info("[REALTIME] Failed. Message: %s.",
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
                    logging.info("[REALTIME] Failed. Message: %s.",
                                 ErrorCode.ERROR_MESSAGE[status])
                    self.write_ret(status)
                    self.finish()
                    return
                else:
                    tid = terminal.tid      
                    location = QueryHelper.get_location_info(tid, self.db, self.redis)

                    # check and make name valid
                    if location and location['name'] is None:
                        location['name'] = ''                            
                    # check and make clatclon valid
                    locations = [location,] 
                    locations = get_locations_with_clatlon(locations, self.db) 
                    location = locations[0]

                    if (location and location.clatitude and location.clongitude):
                        res = dict(lon=location.get('longitude', 0),
                                   lat=location.get('latitude', 0),
                                   clon=location.get('clongitude', 0),
                                   clat=location.get('clatitude', 0),
                                   timestamp=location.get('timestamp',0),
                                   name=location.get('name',''))
                 
            self.write_ret(status,
                           dict_=dict(res=res))

        except Exception as e:
            logging.exception("[REALTIME] sid: %s. Exception: %s",
                              mobile, e.args)
            status = ErrorCode.FAILED
            self.write_ret(status)     
