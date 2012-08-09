#! /usr/bin/env python

import logging
import os.path
import site

TOP_DIR_ = os.path.abspath(os.path.join(__file__, "../../.."))
site.addsitedir(os.path.join(TOP_DIR_, "libs"))

import time, datetime

from celery.decorators import task
from celery.task.base import Task
from tornado.options import options, define, parse_command_line
from tornado.ioloop import IOLoop

from db_.mysql import get_connection
from utils.mymemcached import MyMemcached
from helpers.confhelper import ConfHelper
from helpers.smshelper import SMSHelper
from helpers.queryhelper import QueryHelper
from utils.misc import get_terminal_sessionID_key, get_terminal_address_key,\
                       get_name_cache_key
from codes.smscode import SMSCode

if not 'conf' in options:
    define('conf', default=os.path.join(TOP_DIR_, "conf/global.conf"))

def get_tname(dev_id, db, memcached):
    key = get_name_cache_key(dev_id)
    name = memcached.get(key)
    if not name:
        t = db.get("SELECT alias FROM T_TERMINAL_INFO"
                   "  WHERE tid = %s", dev_id)
        name = t.alias
        memcached.set(key, name)
    name = name if name else dev_id
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
    memcached = MyMemcached()
    d = datetime.datetime.fromtimestamp(time.time())
    t = datetime.datetime.combine(datetime.date(d.year, d.month, d.day), datetime.time(0, 0))
    # get today 0:00:00
    tday = int(time.mktime(t.timetuple()))
    # 86400s: 24h
    yday = tday - 86400 
    terminals = db.query("SELECT id, tid, service_status"
                         "  FROM T_TERMINAL_INFO"
                         "  WHERE endtime BETWEEN %s AND %s"
                         "     OR service_status = 0",
                         yday, tday)
    for terminal in terminals:
        terminal_sessionID_key = get_terminal_sessionID_key(terminal.tid)
        terminal_status_key = get_terminal_address_key(terminal.tid)
        # send sms to user, after 9 hours.
        memcached.set(terminal_sessionID_key, 1)
        if memcached.get(terminal_sessionID_key):
            name = get_tname(terminal.tid, db, memcached)
            sms = SMSCode.SMS_SERVICE_STOP % (name)
            sms_to_user(terminal.tid, sms, db)
            #IOLoop.instance().add_timeout(int(time.time()) + 120,
            #                              lambda: sms_to_user(terminal.tid, sms, db))
        keys = [terminal_sessionID_key, terminal_status_key]
        memcached.delete_multi(keys)
        logging.error("[CELERY] Expired terminal: %s", terminal.tid)
        if terminal.service_status != '0':
            db.execute("UPDATE T_TERMINAL_INFO"
                       "  SET service_status = 0"
                       "  WHERE id = %s", terminal.id)
        
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
