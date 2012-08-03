#! /usr/bin/env python

import logging
import os.path
import site

TOP_DIR_ = os.path.abspath(os.path.join(__file__, "../../.."))
site.addsitedir(os.path.join(TOP_DIR_, "libs"))

import time

from celery.decorators import task
from celery.task.base import Task
from tornado.options import options, define, parse_command_line

from db_.mysql import get_connection
from utils.mymemcached import MyMemcached
from helpers.confhelper import ConfHelper
from utils.misc import get_terminal_sessionID_key

if not 'conf' in options:
    define('conf', default=os.path.join(TOP_DIR_, "conf/global.conf"))

def execute():
    """
    check expired terminals.
    conditions: service_status and endtime
    """
    ConfHelper.load(options.conf)
    db = get_connection()
    memcached = MyMemcached()
    terminals = db.query("SELECT id, tid, service_status, endtime"
                         "  FROM T_TERMINAL_INFO")
    for terminal in terminals:
        if (terminal.service_status == '0' or terminal.endtime <= time.time()):
            terminal_sessionID_key = get_terminal_sessionID_key(terminal.tid)
            memcached.delete(terminal_sessionID_key)
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
