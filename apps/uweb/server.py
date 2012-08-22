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
from Queue import PriorityQueue

import tornado.httpserver
import tornado.ioloop
import tornado.web
from tornado.options import define, options
define('port', type=int, default=8000)
define('conf', default=os.path.join(TOP_DIR_, "conf/global.conf"))
# deploy or debug
define('mode', default='deploy')
# use warning for deployment
options['logging'].set('info')

from db_.mysql import DBConnection
from utils.myredis import MyRedis
from constants.MEMCACHED import ALIVED

from handlers.captcha import CaptchaHandler
from handlers.login import LoginHandler, LogoutHandler, WAPTransferHandler, IOSHandler, AndroidHandler
from handlers.register import RegisterHandler
from handlers.terminallist import TerminalListHandler
from handlers.car import SwitchCarHandler
from handlers.lastinfo import LastInfoHandler
from handlers.worker import WorkerPool
from handlers.main import MainHandler
from handlers.track import TrackHandler
from handlers.track import TrackBackHandler
from handlers.event import EventHandler
from handlers.realtime import RealtimeHandler
from handlers.remote import RemoteHandler
from handlers.defend import DefendHandler
from handlers.terminal import TerminalHandler
from handlers.password import PasswordHandler
from handlers.detail import DetailHandler

from handlers.sms import SMSHandler

from utils.dotdict import DotDict
from helpers.confhelper import ConfHelper


class Application(tornado.web.Application):

    def __init__(self, debug=False):
        handlers = [
            # NOTE: the order is important, the first matched pattern is used!!!
            (r"/", MainHandler),
            (r"/login/*", LoginHandler),
            #(r"/register/*", RegisterHandler),
            (r"/terminallist/*", TerminalListHandler),
            (r"/captcha", CaptchaHandler),
            (r"/logout/*", LogoutHandler),
            (r"/switchcar/(\S+)/*", SwitchCarHandler),
            (r"/lastinfo/(\S+)/*", LastInfoHandler),
            (r"/track/*", TrackHandler),
            (r"/trackback/(\S+)/*", TrackBackHandler),
            (r"/event/*", EventHandler),
            (r"/realtime/*", RealtimeHandler),
            (r"/defend/*", DefendHandler),
            (r"/remote/*", RemoteHandler),
            (r"/terminal/*", TerminalHandler),
            (r"/password/*", PasswordHandler),
            (r"/detail/*", DetailHandler),


            (r"/wap/*", WAPTransferHandler),
            (r"/android/*", WAPTransferHandler),
            (r"/ios/*", IOSHandler),

            # accept sms from sms proxy
            (r"/sms/mo/*", SMSHandler),
            
        ]

        settings = dict(
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            cookie_secret="s8g1gVxKOiQoZptLRi2nSuXmiK2ThYJJBSHIUHnqoUw=",
            login_url="/login",
            debug=debug,
            app_name="CLWUWEB",
        )

        tornado.web.Application.__init__(self, handlers, **settings)
        self.queue = PriorityQueue()
        self.db = DBConnection().db
        self.redis = MyRedis()
        self.redis.setvalue('is_alived', ALIVED)


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
    worker_pool = None
    try:
        ConfHelper.load(options.conf)
        app = Application(debug=debug_mode)

        worker_pool = WorkerPool(app.queue, int(ConfHelper.UWEB_CONF.workers))

        http_server = tornado.httpserver.HTTPServer(app, xheaders=True)
        http_server.listen(options.port)
        logging.warn("[uweb] running on: localhost:%d", options.port)
        tornado.ioloop.IOLoop.instance().start()
    except KeyboardInterrupt:
        logging.error("Ctrl-C is pressed.")
    except:
        logging.exception("[uweb] Exit Exception")
    finally:
        logging.warn("[uweb] shutdown...")
        shutdown(worker_pool, http_server)
        logging.warn("[uweb] stopped. Bye!")

if __name__ == "__main__":
    main()
