#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import os
import site
import time

TOP_DIR_ = os.path.abspath(os.path.join(__file__, "../../.."))
site.addsitedir(os.path.join(TOP_DIR_, "libs"))

import datetime
from dateutil.relativedelta import relativedelta
from tornado.options import options, define, parse_command_line

from db_.mysql import get_connection
from helpers.confhelper import ConfHelper
from utils.dotdict import DotDict
from utils.misc import DUMMY_IDS
from helpers.lbmphelper import get_clocation_from_ge 

if not 'conf' in options:
    define('conf', default=os.path.join(TOP_DIR_, "conf/global.conf"))

class DBTask(object):

    def __init__(self):
        self.db = get_connection()

    def __del__(self):
        self.finish()

    def finish(self):
        if self.db:
            self.db.close()

    def update_clatclon(self):
        # get the points without invalid clatlon within 5 minutes, and try to provide
        # valid clatlon for them
        logging.info("[CLERY] dbtask update clatclon started.")
        points = self.db.query("SELECT id, latitude, longitude, clatitude, clongitude"
                               "  FROM T_LOCATION"
                               "  WHERE (clatitude = 0 or clongitude =0) "
                               "  AND latitude != 0 AND longitude !=0 "
                               "  AND timestamp > %s",
                               int(time.time())-60*5)

        logging.info("[CLERY] the number of points without valid claton: %s.", len(points))
        for point in points:
            time.sleep(1)
            clat, clon = get_clocation_from_ge(point['latitude'], point['longitude']) 
            self.db.execute("UPDATE T_LOCATION"
                            "  SET clatitude = %s, clongitude = %s"
                            "  WHERE id = %s",
                            clat, clon, point['id'])

def update_clatclon():
    dbt = DBTask()
    dbt.update_clatclon()

if __name__ == "__main__":
    ConfHelper.load(options.conf)
    parse_command_line() 
    update_clatclon()
else:
    try:
        from celery.decorators import task
        update_clatclon = task(ignore_result=True)(update_clatclon)
    except Exception as e: 
        logging.exception("[CELERY] dbtask failed. Exception: %s", e.args)
