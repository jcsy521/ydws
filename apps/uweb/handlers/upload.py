# -*- coding: utf-8 -*-

"""This module is designed for YDWQ to upload packet. 
"""

import logging

from tornado.escape import json_decode
import tornado.web

from helpers.queryhelper import QueryHelper 
from utils.public import (insert_location, 
     update_terminal_info_ydwq, update_terminal_status, record_attendance)
from utils.dotdict import DotDict
from codes.errorcode import ErrorCode
from constants import UWEB 
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
            sn = data.sn
            category = int(data.category)
            location = data.location
            gps = int(data.gps)
            gsm = int(data.gsm)
            pbat = int(data.pbat)
            attendance_time = data.get('attendance_time', '')
            logging.info("[UWEB] upload request: %s", 
                         data)
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            logging.exception("[UWEB] Invalid data format. Exception: %s, data: %s",
                              e.args, self.request.body)
            self.write_ret(status)
            return

        try:
            terminal = self.db.get("SELECT id, service_status, mobile"
                                   "  FROM T_TERMINAL_INFO"
                                   "  WHERE mobile = %s"
                                   "  AND sn = %s"
                                   "  AND service_status = %s"
                                   "  AND biz_type = %s LIMIT 1",
                                   mobile, sn, UWEB.SERVICE_STATUS.ON,
                                   UWEB.BIZ_TYPE.YDWQ)
            if not terminal: 
                status = ErrorCode.ACCOUNT_NOT_MATCH 
                logging.info('mobile: %s, sn: %s not match, drop it.', 
                              mobile, sn)
                self.write_ret(status)
                return
            
            terminal = QueryHelper.get_terminal_by_tmobile(mobile, self.db)
            tid = terminal['tid']
            # NOTE: location may be a dict or list
            if type(location) != list:
                locations = [location,]
            else:
                locations = location

            if category == UWEB.UPLOAD_CATEGORY.HEARTBEAT:
                pass
            elif category == UWEB.UPLOAD_CATEGORY.LOCATION:
                for location in locations:
                    location = DotDict(dev_id=tid,
                                       lat=location['clatitude'],
                                       lon=location['clongitude'],
                                       alt=0,
                                       cLat=location['clatitude'],
                                       cLon=location['clongitude'],
                                       gps_time=location['timestamp'],
                                       name=location.get('name', ''),
                                       category=1,
                                       type=int(location['type']),
                                       speed=location['speed'],
                                       degree=location['degree'],
                                       cellid='',
                                       locate_error=int(location['locate_error']))
                    insert_location(location, self.db, self.redis)
            elif category == UWEB.UPLOAD_CATEGORY.ATTENDANCE:
                location = locations[0] if len(locations) >= 1 else None
                if location:
                    location = DotDict(dev_id=tid,
                                       lat=location['clatitude'],
                                       lon=location['clongitude'],
                                       alt=0,
                                       cLat=location['clatitude'],
                                       cLon=location['clongitude'],
                                       gps_time=location['timestamp'],
                                       name=location.get('name', ''),
                                       category=1,
                                       type=int(location['type']),
                                       speed=location['speed'],
                                       degree=location['degree'],
                                       cellid='',
                                       locate_error=int(location['locate_error']))
                    lid = insert_location(location, self.db, self.redis)
                    a_info=dict(mobile=mobile,
                                comment=u'',
                                timestamp=attendance_time if attendance_time else location['gps_time'],
                                lid=lid)
                    record_attendance(self.db, a_info)
                else:
                    logging.error("[UWEB] Invalid attendance data, location is missed.")
            else: 
                #TODO: handle power-event  
                location = locations[0] if len(locations) >= 1 else None
                if location:
                    location = DotDict(dev_id=tid,
                                       lat=location['clatitude'],
                                       lon=location['clongitude'],
                                       alt=0,
                                       cLat=location['clatitude'],
                                       cLon=location['clongitude'],
                                       gps_time=location['timestamp'],
                                       name=location.get('name', ''),
                                       category=1,
                                       type=int(location['type']),
                                       speed=location['speed'],
                                       degree=location['degree'],
                                       cellid='',
                                       locate_error=int(location['locate_error']))
                    lid = insert_location(location, self.db, self.redis)
                    #a_info=dict(mobile=mobile,
                    #            comment=u'',
                    #            timestamp=attendance_time if attendance_time else location['gps_time'],
                    #            lid=lid)
                    #record_attendance(self.db, a_info)
                
            t_info = DotDict(gps=gps, 
                             gsm=gsm,
                             login=1,
                             pbat=pbat,
                             tid=tid)

            update_terminal_info_ydwq(self.db, self.redis, t_info)
            update_terminal_status(self.redis, tid)
                
            self.write_ret(status)
        except Exception as e:
            logging.exception("[UWEB] tmobile:%s upload failed. Exception: %s",
                              mobile, e.args)
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)
