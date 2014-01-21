#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os.path
import site
import logging
import time
import signal
import thread
from Queue import PriorityQueue

import tornado.httpserver
import tornado.ioloop
import tornado.web
from tornado.options import define, options, parse_command_line

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
from handlers.worker import WorkerPool
from business.mt import MT


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
        self.queue = PriorityQueue()


def shutdown(pool, server):
    try:
        if pool:
            pool.clear()

        if server:
            # old version of tornado does not support stop
            if hasattr(server, 'stop'):
                server.stop()
            tornado.ioloop.IOLoop.instance().stop
    except:
        pass

def add_sms_to_queue_thread(queue):
    logging.info("[SMS] add_sms_to_queue thread started.")
    #time interval 3 second
    INTERVAL = 0.1 
    status = ErrorCode.FAILED
    mt = MT(queue)
    try:
        while True:
            time.sleep(INTERVAL)
            if queue.qsize() > 0:
                continue
            status = mt.add_sms_to_queue()
            if status == ErrorCode.SUCCESS:
                INTERVAL = 0.1 
            else:
                INTERVAL = INTERVAL * 2
                if INTERVAL > 600:
                    INTERVAL = 600
    except Exception as e:
        logging.exception("[SMS] Start add_sms_to_queue thread failed: %s", 
                          e.args)

def main():
    parse_command_line()
    if options.mode.lower() == "debug":
        debug_mode = True
    else:
        debug_mode = False

    http_server = None
    try:
        ConfHelper.load(options.conf)
        app = Application(debug=debug_mode)
        http_server = tornado.httpserver.HTTPServer(app, xheaders=True)
        worker_pool = WorkerPool(app.queue, int(ConfHelper.SMS_CONF.workers))

        thread.start_new_thread(add_sms_to_queue_thread, (app.queue,))

        http_server.listen(options.port)
        logging.warn("[SMS] running on: localhost:%d", options.port)
        tornado.ioloop.IOLoop.instance().start()
    except KeyboardInterrupt:
        logging.error("Ctrl-C is pressed.")
    except:
        logging.exception("[SMS] exit exception")
    finally:
        logging.warn("[SMS] shutdown...")
        if http_server:
            shutdown(worker_pool, http_server)
        logging.warn("[SMS] Stopped. Bye!")

if __name__ == "__main__":
    main()
  
