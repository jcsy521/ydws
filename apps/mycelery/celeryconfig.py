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

CELERY_IMPORTS = ("gatewaytask",)

CELERYBEAT_SCHEDULE = {

   "gatewaytask": {
       "task": "gatewaytask.execute",
       # 1:00AM every day 
       "schedule": crontab(minute=0, hour=1), 
   },

}
