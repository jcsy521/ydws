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
try:
    options['logging'].set('info')
except:
    options.logging='info'

from db_.mysql import DBConnection
from utils.myredis import MyRedis
from utils.dotdict import DotDict
from helpers.confhelper import ConfHelper
from constants.MEMCACHED import ALIVED

#from handlers.main import MainHandler
from handlers.weixin import WeixinHandler
from handlers.worker import WorkerPool
from handlers.main import MainHandler
from handlers.base import BaseHandler
from handlers.bind import BindHandler, UnBindHandler
from handlers.terminals import TerminalsHandler
from handlers.event import EventHandler


class Application(tornado.web.Application):

    def __init__(self, debug=False):
        handlers = [
            # NOTE: the order is important, the first matched pattern is used!!!
            #(r"/", MainHandler),
            (r"/", WeixinHandler),
            (r"/bind", BindHandler),
            (r"/unbind", UnBindHandler),
            (r"/weixin", WeixinHandler),
            (r"/terminals", TerminalsHandler),
            (r"/event", EventHandler),

        ]

        settings = dict(
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            server_path=os.path.dirname(__file__),
            activity_path="/static/activity/pic/",
            avatar_path="/static/avatar/",
            cookie_secret="s8g1gVxKOiQoZptLRi2nSuXmiK2ThYJJBSHIUHnqoUw=",
            login_url="/",
            #debug=debug,
            app_name="ACBWEIXIN",
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
        logging.warn("[WEIXIN] running on: localhost:%d", options.port)
        tornado.ioloop.IOLoop.instance().start()
    except KeyboardInterrupt:
        logging.error("Ctrl-C is  pressed.")
    except:
        logging.exception("[uweb] Exit Exception")
    finally:
        logging.warn("[WEIXIN] shutdown...")
        shutdown(worker_pool, http_server)
        logging.warn("[WEIXIN] stopped. Bye!")

if __name__ == "__main__":
    main()
