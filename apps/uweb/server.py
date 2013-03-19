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

from handlers.captcha import CaptchaHandler, CaptchaSmsHandler
from handlers.login import LoginHandler, LogoutHandler, IOSHandler, AndroidHandler, IOSLogoutHandler, AndroidLogoutHandler
from handlers.checkupdate import CheckUpdateAndroidHandler, CheckUpdateIOSHandler
from handlers.car import SwitchCarHandler
from handlers.wakeup import WakeupHandler
from handlers.register import RegisterHandler
from handlers.lastinfo import LastInfoHandler, LastInfoCorpHandler
from handlers.worker import WorkerPool
from handlers.main import MainHandler
from handlers.track import TrackHandler, TrackLQHandler
from handlers.event import EventHandler
from handlers.realtime import RealtimeHandler
from handlers.defend import DefendHandler
from handlers.group import GroupHandler, GroupTransferHandler
from handlers.corp import CorpHandler
from handlers.terminal import TerminalHandler, TerminalCorpHandler
from handlers.statistic import StatisticHandler
from handlers.mileage import MileageHandler
from handlers.password import PasswordHandler, PasswordCorpHandler, PasswordOperHandler
from handlers.profile import ProfileHandler, ProfileCorpHandler, ProfileOperHandler
from handlers.smsoption import SMSOptionHandler
from handlers.appsettings import AppSettingsHandler
from handlers.unbind import UNBindHandler
from handlers.feedback import FeedBackHandler
from handlers.download import DownloadHandler, DownloadTerminalHandler, DownloadSmsHandler
from handlers.about import AboutHandler
from handlers.instruction import WebInsHandler, AndroidInsHandler, IOSInsHandler, SMSInsHandler 
from handlers.servicesterms import ServicesTermsHandler
from handlers.helper import HelperHandler 
from handlers.wapimg import WapImgHandler
from handlers.tinyurl import TinyURLHandler
from handlers.delegation import DelegationHandler
from handlers.checker import CheckTMobileHandler, CheckCNumHandler, CheckCNameHandler
from handlers.checker import CheckOperMobileHandler
from handlers.friendlink import FriendLinkHandler
from handlers.batch import BatchImportHandler
from handlers.batch import BatchDeleteHandler
from handlers.batch import BatchJHHandler
from handlers.operator import OperatorHandler

from utils.dotdict import DotDict
from helpers.confhelper import ConfHelper


class Application(tornado.web.Application):

    def __init__(self, debug=False):
        handlers = [
            # NOTE: the order is important, the first matched pattern is used!!!
            (r"/", MainHandler),
            (r"/login/*", LoginHandler),
            (r"/checkupdate/ios/*", CheckUpdateIOSHandler),
            (r"/checkupdate/*", CheckUpdateAndroidHandler),
            (r"/captcha", CaptchaHandler),
            (r"/captchasms", CaptchaSmsHandler),
            (r"/logout/*", LogoutHandler),
            (r"/switchcar/(\S+)/*", SwitchCarHandler),
            (r"/wakeup/*", WakeupHandler),
            (r"/lastinfo/corp/*", LastInfoCorpHandler),
            (r"/lastinfo/*", LastInfoHandler),
            (r"/track/*", TrackHandler),
            (r"/tracklq/*", TrackLQHandler),
            (r"/event/*", EventHandler),
            (r"/realtime/*", RealtimeHandler),
            (r"/defend/*", DefendHandler),
            (r"/terminal/*", TerminalHandler),
            (r"/statistic/*", StatisticHandler),
            (r"/mileage/*", MileageHandler),
            (r"/terminal/corp/*", TerminalCorpHandler),
            (r"/password/*", PasswordHandler),
            (r"/password/corp/*", PasswordCorpHandler),
            (r"/password/oper/*", PasswordOperHandler),
            (r"/profile/*", ProfileHandler),
            (r"/profile/corp/*", ProfileCorpHandler),
            (r"/profile/oper/*", ProfileOperHandler),
            (r"/smsoption/*", SMSOptionHandler),
            (r"/appsettings/*", AppSettingsHandler),
            (r"/unbind/*", UNBindHandler),

            (r"/about/*", AboutHandler),

            (r"/feedback/*", FeedBackHandler),

            (r"/instruction/web/*", WebInsHandler),
            (r"/instruction/android/*", AndroidInsHandler),
            (r"/instruction/ios/*", IOSInsHandler),
            (r"/instruction/sms/*", SMSInsHandler),

            (r"/download/terminal/*", DownloadTerminalHandler),
            (r"/download/*", DownloadHandler),
            (r"/downloadsms/*", DownloadSmsHandler),

            (r"/servicesterms/*", ServicesTermsHandler),
            (r"/helper/*", HelperHandler),

            # for android 
            (r"/android/*", AndroidHandler),
            (r"/logout/android/*", AndroidLogoutHandler),

            # for ios
            (r"/ios/*", IOSHandler),
            (r"/logout/ios/*", IOSLogoutHandler),

            (r"/register/*", RegisterHandler),
            
            # for wap
            (r"/wapimg/*", WapImgHandler),

            # tinyurl
            (r"/tl/(\S+)/*", TinyURLHandler),

            # a secret url for delegation: uid/tid/sim, sign is provided via
            # ?s=xxxx
            (r"/delegation/5Luj5a6i5pON5L2c/(.*)/(.*)/(.*)/*", DelegationHandler),
            
            (r"/checktmobile/(\d+)/*", CheckTMobileHandler),
            (r"/checkcnum/(\S+)/*", CheckCNumHandler),
            (r"/checkcname/(\S+)/*", CheckCNameHandler),
            (r"/checkopermobile/(\d+)/*", CheckOperMobileHandler),

            (r"/friendlink/*", FriendLinkHandler),

            # for corp
            (r"/group/*", GroupHandler),
            (r"/changegroup/*", GroupTransferHandler),
            (r"/corp/*", CorpHandler),
            (r"/batch/import/*", BatchImportHandler),
            (r"/batch/delete/*", BatchDeleteHandler),
            (r"/batch/JH/*", BatchJHHandler),
            (r"/operator/*", OperatorHandler),
        ]

        settings = dict(
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            cookie_secret="s8g1gVxKOiQoZptLRi2nSuXmiK2ThYJJBSHIUHnqoUw=",
            login_url="/login",
            debug=debug,
            app_name="ACBUWEB",
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
