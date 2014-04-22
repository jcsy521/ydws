# -*- coding: utf-8 -*-

import logging
import os
import site
import time

TOP_DIR_ = os.path.abspath(os.path.join(__file__, "../../.."))
site.addsitedir(os.path.join(TOP_DIR_, "libs"))

from db_.mysql import DBConnection
from db_.mysql import get_connection
from helpers.smshelper import SMSHelper
from helpers.emailhelper import EmailHelper 
from helpers.confhelper import ConfHelper
from codes.smscode import SMSCode
from helpers.lbmphelper import get_clocation_from_ge, get_locations_with_clatlon

class CheckDB(object):

    def __init__(self):
        self.db = get_connection()

    def __del__(self):
        self.finish()

    def finish(self):
        if self.db:
            self.db.close()

    def update_clatclon(self):
        # get the points without invalid clatlon within 5 second, and try to provide
        # valid clatlon for them
        logging.info("[CLERY] dbtask update clatclon started.")
        _now_time = int(time.time())

        points = self.db.query("SELECT id, latitude, longitude, clatitude, clongitude, type, timestamp"
                               "  FROM T_LOCATION"
                               "  WHERE (clatitude = 0 or clongitude =0) "
                               "  AND latitude != 0 AND longitude !=0 "
                               "  AND (timestamp between %s and %s)",
                               _now_time-5, _now_time)

        logging.info("[CLERY] Time: %s, the number of points without valid claton: %s.", 
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

