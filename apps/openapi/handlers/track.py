# -*- coding: utf-8 -*-

"""This module is designed for track of Open API.
"""

import logging

import tornado.web
from tornado.escape import json_decode

from utils.dotdict import DotDict
from codes.openapi_errorcode import ErrorCode
from constants import UWEB, OPENAPI
from helpers.queryhelper import QueryHelper
from helpers.openapihelper import OpenapiHelper 
from helpers.lbmphelper import get_locations_with_clatlon
from utils.track import get_track

from base import BaseHandler

class TrackHandler(BaseHandler):

    """Handle the track of terminal.

    :url /openapi/track
    """

    @tornado.web.removeslash
    def post(self):
        """Get locations in same period. 
        """
        status = ErrorCode.SUCCESS
        res = []
        try:
            data = DotDict(json_decode(self.request.body))
            mobile = str(data.mobile)
            start_time = int(data.start_time)
            end_time = int(data.end_time)
            token = data.token
            logging.info("[TRACK] Request, data:%s", data)
        except Exception as e:
            status = ErrorCode.DATA_FORMAT_INVALID
            logging.exception("[TRACK] Invalid data format, body: %s, mobile: %s.",
                              self.request.body, mobile)
            self.write_ret(status)
            return

        try:
            status = self.basic_check(token, mobile)                          
            if status != ErrorCode.SUCCESS:
                self.write_ret(status)
                return

            if (end_time - start_time) > OPENAPI.LIMIT.TRACK_INTERVAL:
                status = ErrorCode.LOCATION_EXCEED
                self.write_ret(status)              
                return 

            terminal = QueryHelper.get_terminal_by_tmobile(mobile, self.db)
            tid = terminal.tid
            track = get_track(self.db, self.redis, tid, start_time, end_time, cellid=True)
            for t in track:
                if (t and t.clatitude and t.clongitude):
                    d = dict(lon=t.get('longitude', 0),
                             lat=t.get('latitude', 0),
                             clon=t.get('clongitude', 0),
                             clat=t.get('clatitude', 0),
                             timestamp=t.get('timestamp',0),
                             name=t.get('name',''),
                             type=t.get('type',0))
                    res.append(d)
                else:
                    pass 
            if len(res) > OPENAPI.LIMIT.TRACK:
                logging.info("[UWEB] Track is too large, just provide the latest part.")
                res = res[-OPENAPI.LIMIT.TRACK:]
            
            self.write_ret(status,   
                           dict_=dict(res=res))

        except Exception as e:
            logging.exception("[TRACK] Track failed. mobile: %s. Exception: %s",
                              mobile, e.args)
            status = ErrorCode.FAILED
            self.write_ret(status)
