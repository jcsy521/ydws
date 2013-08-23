#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os.path
import site
 
TOP_DIR_ = os.path.abspath(os.path.join(__file__, "../../.."))
site.addsitedir(os.path.join(TOP_DIR_, "libs"))


import logging
import thread
import time

import tornado.httpserver
import tornado.web
import tornado.ioloop
from tornado.options import options,define

define("port",default=6001,type=int)
if 'conf' not in options:
    define('conf', default=os.path.join(TOP_DIR_, "conf/global.conf"))
define('mode', default='deploy')
options['logging'].set('warning')


from handlers.logout import LogoutHandler
from handlers.login import LoginHandler
#from handlers.confhelper import ConfHelper
from handlers.log import Log
from handlers.captcha import CaptchaHandler
from handlers.detail import Detail
from handlers.getlogs import DoFile
from handlers.message import MessageHandler
from handlers.packet import GWPacketHandler
from handlers.battery import GWBatteryHandler
from handlers.scriptManage import DeleteLuaHandler, DownloadLuaHandler, UploadLuaHandler
from handlers.password import LOGPasswordHandler
from helpers.confhelper import ConfHelper
from db_.mysql import DBConnection
from utils.myredis import MyRedis



class Application(tornado.web.Application):

    def __init__(self,debug=False):

        handlers = [
            # NOTE: the order is important, the first matched pattern is used!!!
            (r"/", MainHandler),
            (r"/login", LoginHandler),
            (r"/smssend",MessageHandler),

            (r"/systemlog",Log),
            (r"/detail",Detail),
            (r"/captcha",CaptchaHandler),
            (r"/logout",LogoutHandler),

            (r"/packet",GWPacketHandler),
            (r"/battery",GWBatteryHandler),
            (r"/password",LOGPasswordHandler),
            (r"/uploadluascript",UploadLuaHandler),
            (r"/downloadluascript",DownloadLuaHandler),
            (r"/deleteluascript",DeleteLuaHandler),
            ]

        settings = dict(
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            cookie_secret="s8g1gVxKOiQoZptLRi2nSuXmiK2ThYJJBSHIUHnqoUw=",
            login_url="/login",
            debug=debug,
            app_name="ACBLOGSYSTEM",
        )

        self.redis=MyRedis()        

        tornado.web.Application.__init__(self, handlers, **settings)

class MainHandler(tornado.web.RequestHandler):

    def get(self):
        self.redirect("/login")

class LogSyncer(object):
    # in second. 30 minutes
    INTERVAL = 60 * 30

    def start(self):
        while True:
            try:
                df = DoFile()
                df.dofile() 
                time.sleep(self.INTERVAL)
            except Exception as e:
                logging.error("[LOG] log syncer failed. exception: %s", e.args)

def shutdown(server):
    try:
        # old version of tornado does not support stop
        if hasattr(server, 'stop'):
            server.stop()
        tornado.ioloop.IOLoop.instance().stop()
    except:
        pass

def start_log_syncer():
    logging.info("[LOG] begin to sync logs")
    log_syncer = LogSyncer() 
    log_syncer.start()

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

        http_server = tornado.httpserver.HTTPServer(Application(debug=debug_mode), xheaders=True)
        http_server.listen(options.port)
        thread.start_new_thread(start_log_syncer, ())
        logging.warn("[LOG] running on: localhost:%d", options.port)
        tornado.ioloop.IOLoop.instance().start()
    except KeyboardInterrupt: # todo: SystemExit?
        logging.error("Ctrl-C is pressed.")
    except:
        logging.exception("[LOG] Exit Exception")
    finally:
        logging.warn("[LOG] shutdown...")
        if http_server is not None:
            shutdown(http_server)
        logging.warn("[LOG] stopped. Bye!")


if __name__ == "__main__":
    main()
