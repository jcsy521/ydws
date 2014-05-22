# -*- coding: utf-8 -*-

import os.path
import site

TOP_DIR_ = os.path.abspath(os.path.join(__file__, "../../.."))
site.addsitedir(os.path.join(TOP_DIR_, "libs"))

from datetime import timedelta
from celery.schedules import crontab

from helpers.confhelper import ConfHelper

_conf_file = os.path.join(TOP_DIR_, "conf/global.conf")
ConfHelper.load(_conf_file)

BROKER_HOST = ConfHelper.CELERY_CONF.host
BROKER_PORT = int(ConfHelper.CELERY_CONF.port)
BROKER_USER = ConfHelper.CELERY_CONF.user
BROKER_PASSWORD = ConfHelper.CELERY_CONF.password
BROKER_VHOST = ConfHelper.CELERY_CONF.vhost

CELERY_RESULT_BACKEND = "amqp"

CELERY_DISABLE_RATE_LIMITS = True

# import tasks 
CELERY_IMPORTS = ("admintask","dbtask", "checkertask")

CELERYBEAT_SCHEDULE = {
   "statistic_offline_terminal": {
       "task": "admintask.statistic_offline_terminal",
       # 23:59PM every day
       "schedule": crontab(minute=59, hour=23),
   },

   "statistic_user": {
       "task": "admintask.statistic_user",
       # 23:59PM every day
       "schedule": crontab(minute=30, hour=23),
   },


   "check_poweroff": {
       "task": "checkertask.check_poweroff",
       # every 1 minute 
       "schedule": timedelta(minutes=1),
   },

   "check_track": {
       "task": "checkertask.check_track",
       # every 1 minute 
       "schedule": timedelta(minutes=1),
   },

   "mileage_notify": {
       "task": "checkertask.mileage_notify",
       # 09:59PM every day
       "schedule": crontab(minute=59, hour=9),
   },

   # part 2: for db 
   "update_clatclon": {
       "task": "dbtask.update_clatclon",
       # every 2 minute 
       "schedule": timedelta(minutes=5),
   },


   #"flush": {
   #    "task": "dbtask.flush",
   #    # 1:00AM every day
   #    "schedule": crontab(minute=0, hour=1),
   #},

}
