# -*- coding: utf-8 -*-

import logging
import os
import site
import time

TOP_DIR_ = os.path.abspath(os.path.join(__file__, "../../.."))
site.addsitedir(os.path.join(TOP_DIR_, "libs"))

from db_.mysql import DBConnection
from db_.mysql import get_connection
from db_.mysql import get_connection_push
from helpers.smshelper import SMSHelper
from helpers.emailhelper import EmailHelper 
from helpers.confhelper import ConfHelper
from codes.smscode import SMSCode
from helpers.lbmphelper import get_clocation_from_ge, get_locations_with_clatlon

class CheckDB(object):

    def __init__(self):

        self.db = get_connection()
        self.db_push = get_connection_push()

        self.alarm_size = 100 
        self.mobiles = [13693675352, 
                        18310505991, 
                        15110243861, 
                        13581731204]

        self.emails = ['boliang.guan@dbjtech.com', 
                       'xiaolei.jia@dbjtech.com',
                       'ziqi.zhong@dbjtech.com', 
                       'youbo.sun@dbjtech.com']

    def __del__(self):
        self.finish()

    def finish(self):
        if self.db:
            self.db.close()

    def check_sms(self):
        """Notify administrators when sms to be send is more than alarm_size;
        """
        res = self.db.get("SELECT count(id) as count FROM T_SMS where send_status = -1")
        if res and res['count'] >= self.alarm_size:
            content = SMSCode.SMS_SMS_REPORT % ConfHelper.UWEB_CONF.url_out
            for mobile in self.mobiles:
                SMSHelper.send(mobile, content)
            for email in self.emails:
                EmailHelper.send(email, content) 
            logging.info("[CK] Notify sms queue exception to administrator!")

    def check_push(self):
        """
        """
        res = self.db_push.get("SELECT count(id) as count FROM T_PUSH where status = 1")
        if res and res['count'] >= self.alarm_size:
            content = SMSCode.SMS_PUSH_REPORT % ConfHelper.UWEB_CONF.url_out
            for mobile in self.mobiles:
                SMSHelper.send(mobile, content)
            for email in self.emails:
                EmailHelper.send(email, content) 
            logging.info("[CK] Notify push queue exception to administrator!")

    def update_clatclon(self):
        # get the points without invalid clatlon within 5 second, and try to provide
        # valid clatlon for them
        logging.info("[CK] dbtask update clatclon started.")
        _now_time = int(time.time())

        points = self.db.query("SELECT id, latitude, longitude, clatitude, clongitude, type, timestamp"
                               "  FROM T_LOCATION"
                               "  WHERE (clatitude = 0 or clongitude =0) "
                               "  AND latitude != 0 AND longitude !=0 "
                               "  AND (timestamp between %s and %s)",
                               _now_time-5, _now_time)

        logging.info("[CK] Time: %s, the number of points without valid claton: %s.", 
                     _now_time, len(points))

        get_locations_with_clatlon(points, self.db)
        #for point in points:
        #    time.sleep(0.1)
        #    clats, clons = get_clocation_from_ge([point['latitude'],], [point['longitude'],]) 
        #    clat, clon = clats[0], clons[0]
        #    self.db.execute("UPDATE T_LOCATION"
        #                    "  SET clatitude = %s, clongitude = %s"
        #                    "  WHERE id = %s",
        #                    clat, clon, point['id'])

