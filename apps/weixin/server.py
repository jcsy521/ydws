#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os.path
import site

TOP_DIR_ = os.path.abspath(os.path.join(__file__, "../../.."))
site.addsitedir(os.path.join(TOP_DIR_, "libs"))

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
from utils.dotdict import DotDict
from utils.misc import get_static_hash
from helpers.confhelper import ConfHelper
from constants.MEMCACHED import ALIVED

from handlers.wxinterface import WXInterfaceHandler
class Application(tornado.web.Application):
    def __init__(self, debug=False):
        handlers = [
            (r"/", WXInterfaceHandler)
        ]

        settings = dict(
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            server_path=os.path.dirname(__file__),
            terminal_path="/static/terminal/",
            activity_path="/static/activity/pic/",
            avatar_path="/static/avatar/",
            cookie_secret="s8g1gVxKOiQoZptLRi2nSuXmiK2ThYJJBSHIUHnqoUw=",
            login_url="/login",
            #debug=debug,
            app_name="ACBWEIXIN",
        )

        tornado.web.Application.__init__(self, handlers, **settings)
        self.queue = PriorityQueue()
        self.db = DBConnection().db
        self.redis = MyRedis()
        self.redis.setvalue('is_alived', ALIVED)
        hash_ = get_static_hash(settings.get('static_path'))
        self.redis.setvalue('static_hash', hash_)

def shutdown(pool, server):
    try:
        if pool:
            pool.clear()

        if server:
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
        http_server = tornado.httpserver.HTTPServer(app, xheaders=True)
        http_server.listen(options.port)
        logging.warn("[weixin] running on: localhost:%d", options.port)
        tornado.ioloop.IOLoop.instance().start()
    except KeyboardInterrupt:
        logging.error("Ctrl-C is  pressed.")
    except:
        logging.exception("[weixin] Exit Exception")
    finally:
        logging.warn("[weixin] shutdown...")
        shutdown(worker_pool, http_server)
        logging.warn("[weixin] stopped. Bye!")

if __name__ == "__main__":
    main()
