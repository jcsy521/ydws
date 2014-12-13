#!/usr/bin/env python
# -*- coding: utf-8 -*-
 
import os.path
import site

TOP_DIR_ = os.path.abspath(os.path.join(__file__, "../../.."))
site.addsitedir(os.path.join(TOP_DIR_, "libs"))

# NOTE: why import signal but never used?
# Threads interact strangely with interrupts: the KeyboardInterrupt exception
# will be received by an arbitrary thread. (When the signal module is available,
# interrupts always go to the main thread.)
#     -- http://docs.python.org/library/thread.html#module-thread
import signal
import logging

import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.locale
from tornado.options import define, options
define('port', type=int, default=6331)
define('conf', default=os.path.join(TOP_DIR_, "conf/global.conf"))
# deploy or debug
define('mode', default='deploy')
# use warning for deployment
options['logging'].set('info')

from db_.mysql import DBConnection
from utils.myredis import MyRedis

from utils.dotdict import DotDict
from helpers.confhelper import ConfHelper

from handlers.main import MainHandler

# NOTE: features
from handlers.token import TokenHandler
from handlers.realtime import RealtimeHandler 
from handlers.track import TrackHandler
from handlers.manual import ManualHandler
from handlers.reboot import RebootHandler
from handlers.mileage import MileageHandler

# NOTE: test
from handlers.test import SignHandler

class Application(tornado.web.Application):

    def __init__(self, debug=False):
        handlers = [
            # NOTE: the order is important, the first matched pattern is used!!!
            (r"/", MainHandler),
            # NOTE: features
            (r"/openapi/token/*", TokenHandler),
            (r"/openapi/realtime/*", RealtimeHandler),
            (r"/openapi/track/*", TrackHandler),
            (r"/openapi/manual/*", ManualHandler),
            (r"/openapi/reboot/*", RebootHandler),
            (r"/openapi/mileage/*", MileageHandler),                        

            #NOTE: test
            (r"/openapi/sign/*", SignHandler),
        ]

        settings = dict(
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            server_path=os.path.dirname(__file__),
            debug=debug,
        )

        tornado.web.Application.__init__(self, handlers, **settings)
        self.db = DBConnection().db
        self.redis = MyRedis()
 

def shutdown(server):
    try:
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
    try:
        ConfHelper.load(options.conf)
        app = Application(debug=debug_mode)

        http_server = tornado.httpserver.HTTPServer(app, xheaders=True)
        http_server.listen(options.port)
        logging.warn("[OPENAPI] running on: localhost:%d", options.port)
        tornado.ioloop.IOLoop.instance().start()
    except KeyboardInterrupt:
        logging.error("Ctrl-C is pressed.")
    except:
        logging.exception("[OPENAPI] Exit Exception")
    finally:
        logging.warn("[OPENAPI] shutdown...")
        shutdown(http_server)
        logging.warn("[OPENAPI] stopped. Bye!")

if __name__ == "__main__":
    main()
