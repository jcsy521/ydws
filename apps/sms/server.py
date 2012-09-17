#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os.path
import site
import logging
import time
import thread

import tornado.httpserver
import tornado.ioloop
import tornado.web
from tornado.options import define, options

TOP_DIR_ = os.path.abspath(os.path.join(__file__, "../../.."))
site.addsitedir(os.path.join(TOP_DIR_, "libs"))
define('port', type=int, default=6631)
define('conf', default=os.path.join(TOP_DIR_, "conf/global.conf"))
# deploy or debug
define('mode', default='deploy')
# use info for deployment
options['logging'].set('info')

from helpers.confhelper import ConfHelper
from db_.mysql import DBConnection
from codes.errorcode import ErrorCode

from handlers.mainhandler import MainHandler
from handlers.acbmthandler import ACBMTHandler
from business.mt import MT
from business.mo import MO
from business.status import Status
from business.moacb import MOACB


class Application(tornado.web.Application):

    def __init__(self, debug=False):
        handlers = [
            #the order is important, the first matched pattern is used
            (r'/', MainHandler),
            (r'/sms/mt/*', ACBMTHandler)
        ]

        settings = dict(
            debug=debug,
        )

        tornado.web.Application.__init__(self, handlers, **settings)
        self.db = DBConnection().db


def shutdown(server):
    try:
        # old version of tornado does not support stop
        if hasattr(server, 'stop'):
            server.stop()
        tornado.ioloop.IOLoop.instance().stop
    except:
        pass


def run_send_failed_mt_thread():
    logging.info("Send failed mt thread started.")
    INTERVAL = int(ConfHelper.SMS_CONF.failed_mt_interval)
    status = ErrorCode.FAILED
    mt = MT()
    try:
        while True:
            time.sleep(INTERVAL)
            status = mt.fetch_failed_mt_sms()
            if status == ErrorCode.SUCCESS:
                INTERVAL = ConfHelper.SMS_CONF.failed_mt_interval
            else:
                INTERVAL = INTERVAL * 2
                if INTERVAL > 600:
                    INTERVAL = 600
    except Exception as e:
        logging.exception("Start send failed MT thread failed: %s", e.args)


def run_send_mt_thread():
    logging.info("MT thread started.")
    #time interval 3 second
    INTERVAL = 3
    status = ErrorCode.FAILED
    mt = MT()
    try:
        while True:
            time.sleep(INTERVAL)
            status = mt.fetch_mt_sms()
            if status == ErrorCode.SUCCESS:
                INTERVAL = 3
            else:
                INTERVAL = INTERVAL * 2
                if INTERVAL > 600:
                    INTERVAL = 600
    except Exception as e:
        logging.exception("Start MT thread failed: %s", e.args)
            
            
def run_user_receive_status_thread():
    logging.info("Get user receive status thread started.")
    #time interval 3 second
    INTERVAL = 3
    result = ErrorCode.FAILED
    status = Status()
    try:
        while True:
            time.sleep(INTERVAL)
            result = status.get_user_receive_status()
            if result == ErrorCode.SUCCESS:
                INTERVAL = 3
            else:
                INTERVAL = INTERVAL * 2
                if INTERVAL > 600:
                    INTERVAL = 600
    except Exception as e:
        logging.exception("Start user receive status thread failed: %s", e.args)
            
            
def run_get_mo_from_gateway_thread():
    logging.info("Get mo sms thread started.")
    #time interval 3 second
    INTERVAL = 3
    status = ErrorCode.FAILED
    mo = MO()
    try:
        while True:
            time.sleep(INTERVAL)
            status = mo.get_mo_sms_from_gateway()
            if status == ErrorCode.SUCCESS:
                INTERVAL = 3
            else:
                INTERVAL = INTERVAL * 2
                if INTERVAL > 600:
                    INTERVAL = 600
    except Exception as e:
        logging.exception("Start get mo sms thread failed: %s", e.args)
            
            
def run_send_mo_to_acb_thread():
    logging.info("Send mo to acb thread started.")
    #time interval 1 second
    INTERVAL = 1
    status = ErrorCode.FAILED
    moacb = MOACB()
    try:
        while True:
            time.sleep(INTERVAL)
            status = moacb.fetch_mo_sms()
            if status == ErrorCode.SUCCESS:
                INTERVAL = 1
            else:
                INTERVAL = INTERVAL * 2
                if INTERVAL > 600:
                    INTERVAL = 600
    except Exception as e:
        logging.exception("Start send mo to acb thread failed: %s", e.args)


def main():
    tornado.options.parse_command_line()
    if options.mode.lower() == "debug":
        debug_mode = True
    else:
        debug_mode = False

    http_server = None
    try:
        ConfHelper.load(options.conf)
        application = Application(debug=debug_mode)
        http_server = tornado.httpserver.HTTPServer(application, xheaders=True)
        # create mt thread
        thread.start_new_thread(run_send_mt_thread, ())
        
        # create send failed mt thread
        thread.start_new_thread(run_send_failed_mt_thread, ())
        
        # create user receive status thread
        thread.start_new_thread(run_user_receive_status_thread, ())
        
        # create get mo thread
        thread.start_new_thread(run_get_mo_from_gateway_thread, ())
        
        # create send mo thread
        thread.start_new_thread(run_send_mo_to_acb_thread, ())
        
        http_server.listen(options.port)
        logging.warn("[ACB SMS] running on: localhost:%d", options.port)
        tornado.ioloop.IOLoop.instance().start()
    except KeyboardInterrupt:
        logging.error("Ctrl-C is pressed.")
    except:
        logging.exception("[ACB SMS] exit exception")
    finally:
        logging.warn("[ACB SMS] shutdown...")
        if http_server:
            shutdown(http_server)
        logging.warn("[ACB SMS] Stopped. Bye!")


if __name__ == "__main__":
    main()
  