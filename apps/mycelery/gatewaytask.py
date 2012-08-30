#! /usr/bin/env python

import logging
import os.path
import site

TOP_DIR_ = os.path.abspath(os.path.join(__file__, "../../.."))
site.addsitedir(os.path.join(TOP_DIR_, "libs"))

import time, datetime
from functools import partial

from celery.decorators import task
from celery.task.base import Task
from tornado.options import options, define, parse_command_line

from db_.mysql import get_connection
from utils.myredis import MyRedis
from helpers.confhelper import ConfHelper
from helpers.smshelper import SMSHelper
from helpers.queryhelper import QueryHelper
from constants import GATEWAY
from utils.repeatedtimer import RepeatedTimer 
from utils.misc import get_terminal_sessionID_key, get_terminal_address_key,\
                       get_alias_key
from codes.smscode import SMSCode

if not 'conf' in options:
    define('conf', default=os.path.join(TOP_DIR_, "conf/global.conf"))

def get_tname(dev_id, db, redis):
    key = get_alias_key(dev_id)
    name = redis.getvalue(key)
    if not name:
        t = db.get("SELECT alias, mobile FROM T_TERMINAL_INFO"
                   "  WHERE tid = %s", dev_id)
        name = t.alias if t.alias else t.mobile
        redis.setvalue(key, name)
    if isinstance(name, str):
        name = name.decode("utf-8")

    return name

def sms_to_user(dev_id, sms, db):
    if not sms:
        return

    user = QueryHelper.get_user_by_tid(dev_id, db) 
    if user:
        SMSHelper.send(user.owner_mobile, sms)

def execute():
    """
    check expired terminals.
    conditions: service_status and endtime
    """
    ConfHelper.load(options.conf)
    db = get_connection()
    redis = MyRedis()
    d = datetime.datetime.fromtimestamp(time.time())
    t = datetime.datetime.combine(datetime.date(d.year, d.month, d.day), datetime.time(0, 0))
    # get today 0:00:00
    tday = int(time.mktime(t.timetuple()))
    # 86400s: 24h
    yday = tday - 86400 
    terminals = db.query("SELECT id, tid, mobile, service_status"
                         "  FROM T_TERMINAL_INFO"
                         "  WHERE endtime BETWEEN %s AND %s"
                         "     OR service_status = %s",
                         yday, tday, GATEWAY.SERVICE_STATUS.OFF)
    for terminal in terminals:
        terminal_sessionID_key = get_terminal_sessionID_key(terminal.tid)
        terminal_status_key = get_terminal_address_key(terminal.tid)
        sessionID = redis.getvalue(terminal_sessionID_key)
        status = redis.getvalue(terminal_status_key)
        if sessionID or status:
            keys = [terminal_sessionID_key, terminal_status_key]
            redis.delete(*keys)
            logging.error("[CELERY] Expired terminal: %s, SIM: %s",
                          terminal.tid, terminal.mobile)
            name = get_tname(terminal.tid, db, redis)
            sms = SMSCode.SMS_SERVICE_STOP % (name,)
            send_sms = partial(sms_to_user, *(terminal.tid, sms, db))
            # send sms to user, after 9 hours(daytime).
            r = RepeatedTimer(9 * 60 * 60, send_sms, 1)
            r.start()

        if terminal.service_status != GATEWAY.SERVICE_STATUS.OFF:
            db.execute("UPDATE T_TERMINAL_INFO"
                       "  SET service_status = %s"
                       "  WHERE id = %s", 
                       GATEWAY.SERVICE_STATUS.OFF, terminal.id)
        
    db.close()


if __name__ == "__main__":
    parse_command_line()
    execute()
else:
    try:
        from celery.decorators import task

        execute = task(ignore_result=True)(execute)
    except:
        logging.exception("what's up?")
