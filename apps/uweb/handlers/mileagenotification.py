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


class MileageNotificationHandler(BaseHandler):
    """Mileage notification: distance of per day"""

    @authenticated
    @tornado.web.removeslash
    def get(self):
        """Get mileage notifiction of a terminal.

        @params: tid, is required 
        """
        status = ErrorCode.SUCCESS
        try:
            tid = self.get_argument('tid') 
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            self.write_ret(status)

        try:
            res = QueryHelper.get_mileage_notification_by_tid(tid, self.db)
            self.write_ret(status,
                           dict_=DotDict(res=res))
        except Exception as e:
            logging.exception("[UWEB] Get mileage notification. cid: %s, Exception: %s",
                              self.current_user.cid, e.args)
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)

    @authenticated
    @tornado.web.removeslash
    def put(self):
        """Modify some settings about mileage notification.
        """
        status = ErrorCode.SUCCESS
        try:
            data = DotDict(json_decode(self.request.body))
            logging.info("[UWEB] Mileage notification request: %s, uid: %s, tid: %s", 
                         data, self.current_user.uid, self.current_user.tid)
            tid = data.tid
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            self.write_ret(status)
            return

        try:
            distance_notification = data.get('distance_notification', None)
            day_notification = data.get('day_notification', None)
            assist_mobile =  data.get('assist_mobile', None)

            if distance_notification is not None:
                self.db.execute("UPDATE T_MILEAGE_NOTIFICATION"
                                "  SET distance_notification = %s,"
                                "      notify_count = 0,"
                                "      left_days = 1,"
                                "      set_time = %s"
                                "  WHERE tid = %s",
                                distance_notification,
                                int(time.time()), tid)
            if day_notification is not None:
                self.db.execute("UPDATE T_DAY_NOTIFICATION"
                                "  SET day_notification = %s,"
                                "      notify_count = 0,"
                                "      left_days = 1,"
                                "      set_time = %s"
                                "  WHERE tid = %s",
                                day_notification, 
                                int(time.time()), tid)
            if assist_mobile is not None:
                self.db.execute("UPDATE T_TERMINAL_INFO"
                                "  SET assist_mobile = %s"
                                "  WHERE tid = %s",
                                assist_mobile, tid)
            self.write_ret(status)
        except Exception as e:
            logging.exception("[UWEB] Get mileage notification. Exception: %s",
                              self.current_user.cid, self.current_user.oid, e.args)
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)
