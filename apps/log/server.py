#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os.path
import site
 
TOP_DIR_ = os.path.abspath(os.path.join(__file__, "../../.."))
site.addsitedir(os.path.join(TOP_DIR_, "libs"))

import logging

import tornado.httpserver
import tornado.web
import tornado.ioloop
from tornado.options import options,define
 
from handlers.logout import LogoutHandler
from handlers.login import Login
from handlers.confhelper import ConfHelper
from handlers.log import Log
from handlers.captcha import CaptchaHandler
from handlers.detail import Detail
from handlers.getlogs import DoFile 


define("port",default=6001,type=int)
define('conf', default=os.path.join(TOP_DIR_, "conf/global.conf"))
define('mode', default='deploy')
options['logging'].set('warning')

class Application(tornado.web.Application):

    def __init__(self,debug=False):

        handlers = [
             (r"/",MainHandler),
             (r"/login",Login),
             (r"/systemlog",Log),
             (r"/detail",Detail),
             (r"/captcha",CaptchaHandler),
             (r"/logout",LogoutHandler)
        ]
        
        settings = dict(
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            cookie_secret="s3g2gVxKOiQoZptLRi2nSuXmiK4sThYJJBSHIUHnqoUw=",
            login_url="/login",
            debug=debug,
            app_name="LOGSYSTEM",
        )

        tornado.web.Application.__init__(self, handlers, **settings)

class MainHandler(tornado.web.RequestHandler):

    def get(self):
        self.redirect("/login")

class FileSyncer(object):
    #NOTE: there must are __call__ and __init__

    def __init__(self, debug=False):
        # in milliseconds. 30 minutes.
        self.interval = 1000 * 60 * 1
        #self.interval = 1000 * 60 * 30

    def start(self):
        self.__call__()

    def __call__(self):
        logging.info("[LOG] begin to sync logs")
        df = DoFile()
        df.dofile() 

def shutdown(server):
    try:
        # old version of tornado does not support stop
        if hasattr(server, 'stop'):
            server.stop()
        tornado.ioloop.IOLoop.instance().stop()
    except:
        pass

def _start_agency_syncer():
    file_syncer = FileSyncer()
    task = tornado.ioloop.PeriodicCallback(file_syncer,
                                           file_syncer.interval) 
    task.start()

def main():
    tornado.options.parse_command_line()
    if not ('port' in options and 'conf' in options):
        import sys
        usage()
        sys.exit(1)

    http_server = None
    try:
        ConfHelper.load(options.conf)
        http_server = tornado.httpserver.HTTPServer(Application(debug=True), xheaders=True)
        http_server.listen(options.port)
        _start_agency_syncer()
        logging.warn("[log_monitor] running on: localhost:%d", options.port)
        tornado.ioloop.IOLoop.instance().start()
    except KeyboardInterrupt: # todo: SystemExit?
        logging.error("Ctrl-C is pressed.")
    except:
        logging.exception("[log_monitor] Exit Exception")
    finally:
        logging.warn("[log_monitor] shutdown...")
        if http_server is not None:
            shutdown(http_server)
        logging.warn("[log_monitor] stopped. Bye!")

if __name__ == "__main__":
    main()
