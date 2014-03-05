# -*- coding: utf-8 -*-

import logging

from tornado.escape import json_decode, json_encode
import tornado.web

from helpers.queryhelper import QueryHelper 
from helpers.confhelper import ConfHelper
from utils.misc import DUMMY_IDS_STR, DUMMY_IDS, safe_unicode, str_to_list, get_terminal_info_key, get_tid_from_mobile_ydwq
from utils.public import insert_location, update_terminal_info, update_terminal_status
from utils.dotdict import DotDict
from codes.errorcode import ErrorCode
from constants import UWEB, EVENTER 
from base import BaseHandler

class UploadHandler(BaseHandler):
    """Get various events for web request."""

    @tornado.web.removeslash
    def post(self):
        """Retrive various event.
        """
        status = ErrorCode.SUCCESS
        try:
            data = DotDict(json_decode(self.request.body))
            mobile = data.mobile
            category = int(data.category)
            location = data.location
            gps = int(data.gps)
            gsm = int(data.gsm)
            pbat = int(data.pbat)
            logging.info("[UWEB] upload request: %s", 
                         data)
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            logging.exception("[UWEB] Invalid data format. Exception: %s",
                              e.args)
            self.write_ret(status)
            return

        try:
            tid = get_tid_from_mobile_ydwq(mobile)
            if category == UWEB.UPLOAD_CATEGORY.HEARTBEAT:
                pass
            elif category == UWEB.UPLOAD_CATEGORY.LOCATION:
                location = DotDict(dev_id=tid,
                                    lat=location['clatitude'],
                                    lon=location['clongitude'],
                                    alt=0,
                                    cLat=location['clatitude'],
                                    cLon=location['clongitude'],
                                    gps_time=location['timestamp'],
                                    name=location['name'],
                                    category=1,
                                    type=0,
                                    speed=location['speed'],
                                    degree=location['degree'],
                                    cellid='',
                                    locate_error=location['locate_error'])
                insert_location(location, self.db, self.redis)
            else: 
                #TODO: handle power-event  
                pass
                
            t_info = DotDict(gps=gps, 
                             gsm=gsm,
                             login=1,
                             pbat=pbat,
                             tid=tid)

            update_terminal_info(self.db, self.redis, t_info )
            update_terminal_status(self.redis, tid)
                
            self.write_ret(status)
        except Exception as e:
            logging.exception("[UWEB] tmobile:%s upload failed. Exception: %s",
                              mobile, e.args)
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)
