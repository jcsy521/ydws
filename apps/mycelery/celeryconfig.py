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

   # part 1: for admin

   "statistic_online_terminal": {
       "task": "admintask.statistic_online_terminal",
       # 12:00AM every day
       "schedule": crontab(minute=0, hour=12),
   },

   "statistic_offline_terminal": {
       "task": "admintask.statistic_offline_terminal",
       # 23:59PM every day
       "schedule": crontab(minute=59, hour=23),
   },

   "statistic_user": {
       "task": "admintask.statistic_user",
       # 23:59PM every day
       "schedule": crontab(minute=59, hour=23),
   },

   # part 2: for checker 
   #"check_remind": {
   #    "task": "checkertask.check_remind",
   #    # 12:00AM every day
   #    #"schedule": crontab(minute=0, hour=12),
   #    "schedule": crontab(minute=32, hour=10),
   #},

   "send_offline_remind_sms": {
       "task": "checkertask.send_offline_remind_sms",
       #  12:00AM every day 
       "schedule": crontab(minute=0, hour=12),
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

   # part 2: for db 
   "update_clatclon": {
       "task": "dbtask.update_clatclon",
       # every 5 minute 
       "schedule": timedelta(minutes=5),
   },
}
