#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
What's eventer?

It's a web service, which waits for requests from GFSender or LBMPSener,
which waits for information (PositionInfo and ReportInfo) from GF.
"""

import os.path
import site

TOP_DIR_ = os.path.abspath(os.path.join(__file__, "../../.."))
site.addsitedir(os.path.join(TOP_DIR_, "libs"))

import logging
from Queue import Queue

import tornado.httpserver
import tornado.ioloop
import tornado.web
from tornado.options import define, options
define('port', type=int, default=5200)
define('conf', default=os.path.join(TOP_DIR_, "conf/global.conf"))
# deploy or debug
define('mode', default='deploy')
# use warning for deployment
options['logging'].set('warning')

from db_.mysql import DBConnection
from utils.myredis import MyRedis
from constants import EVENTER
from helpers.confhelper import ConfHelper

from handlers.worker import WorkerPool

from handlers.main import MainHandler


class Application(tornado.web.Application):

    def __init__(self, debug=False):
        handlers = [
            # NOTE: the order is important, the first matched pattern is used!!!
            (r"/", MainHandler),
        ]

        settings = dict(
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            debug=debug,
        )

        tornado.web.Application.__init__(self, handlers, **settings)

        self.position_queue = Queue()
        self.report_queue = Queue()


def shutdown(pool, server):
    try:
        if pool:
            pool.clear()

        if server:
            # old version of tornado does not support stop
            if hasattr(server, 'stop'):
                server.stop()
            tornado.ioloop.IOLoop.instance().stop()
    except:
        pass


def usage():
    print "python26 server.py --conf=/path/to/conf_file --port=port_num"


def main():
    tornado.options.parse_command_line()
    if not ('port' in options and 'conf' in options):
        import sys
        usage()
        sys.exit(1)

    if options.mode.lower() == "debug":
        debug_mode = True
    else:
        debug_mode = False

    http_server = None
    # creat 2 work_pool, handle diferent package.
    position_worker_pool = None
    report_worker_pool = None
    try:
        ConfHelper.load(options.conf)
        app = Application(debug=debug_mode)
        
        position_worker_pool = WorkerPool(app.position_queue,
                                          int(ConfHelper.EVENTER_CONF.workers),
                                          name=EVENTER.INFO_TYPE.POSITION)
        report_worker_pool = WorkerPool(app.report_queue,
                                        int(ConfHelper.EVENTER_CONF.workers),
                                        name=EVENTER.INFO_TYPE.REPORT)

        http_server = tornado.httpserver.HTTPServer(app, xheaders=True)
        http_server.listen(options.port)
        logging.warn("[eventer] running on: localhost:%d", options.port)
        tornado.ioloop.IOLoop.instance().start()
    except KeyboardInterrupt:
        logging.error("Ctrl-C is pressed.")
    except:
        logging.exception("[eventer] Exit Exception")
    finally:
        logging.warn("[eventer] shutdown...")
        shutdown(position_worker_pool, None)
        shutdown(report_worker_pool, http_server)
        logging.warn("[eventer] Stopped. Bye!")


if __name__ == '__main__':
    main()
