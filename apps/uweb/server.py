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
from utils.misc import get_static_hash 
from helpers.confhelper import ConfHelper
from constants.MEMCACHED import ALIVED

from handlers.captcha import CaptchaHandler, CaptchaSmsHandler, CaptchaImageHandler, CaptchaPasswordHandler
from handlers.login import LoginHandler, LogoutHandler, LoginTestHandler, IOSHandler, IOSLogoutHandler, IOSLoginTestHandler, AndroidHandler, AndroidLogoutHandler, AndroidLoginTestHandler
from handlers.checkupdate import CheckUpdateAndroidHandler, CheckUpdateIOSHandler
from handlers.car import SwitchCarHandler
from handlers.wakeup import WakeupHandler
from handlers.register import RegisterHandler, RegisterBrowserHandler, ReRegisterHandler
from handlers.secregister import SecRegisterHandler
from handlers.lastinfo import LastInfoHandler, LastInfoCorpHandler
from handlers.inclastinfo import IncLastInfoCorpHandler
from handlers.lastposition import LastPositionHandler
from handlers.worker import WorkerPool
from handlers.main import MainHandler
from handlers.track import TrackHandler, TrackDownloadHandler, TrackLQHandler
from handlers.bluetooth import KQLYHandler 
from handlers.event import EventHandler
from handlers.eventperiod import EventPeriodHandler
from handlers.realtime import RealtimeHandler
from handlers.defend import DefendHandler, DefendWeixinHandler
from handlers.group import GroupHandler, GroupTransferHandler
from handlers.corp import CorpHandler
from handlers.terminal import TerminalHandler, TerminalCorpHandler
from handlers.statistic import StatisticHandler, StatisticDownloadHandler, StatisticSingleHandler, StatisticSingleDownloadHandler
from handlers.mileage import MileageHandler, MileageDownloadHandler, MileageSingleDownloadHandler
from handlers.mileagejunior import MileageJuniorHandler
from handlers.mileagesingle import MileageSingleHandler
from handlers.password import PasswordHandler, PasswordCorpHandler, PasswordOperHandler
from handlers.getcaptcha import GetCaptchaHandler, GetCaptchaCorpHandler
from handlers.secgetcaptcha import SecGetCaptchaHandler, SecGetCaptchaCorpHandler
from handlers.profile import ProfileHandler, ProfileCorpHandler, ProfileOperHandler
from handlers.smsoption import SMSOptionHandler, SMSOptionCorpHandler
from handlers.alarmoption import AlarmOptionHandler
from handlers.appsettings import AppSettingsHandler
from handlers.unbind import UNBindHandler
from handlers.share import ShareHandler
from handlers.activity import ActivityHandler
from handlers.announcement import AnnouncementHandler, AnnouncementListHandler
from handlers.activate import ActivationcodeHandler, ActivateHandler 
from handlers.ydwq_activate import YDWQActivateHandler 
from handlers.feedback import FeedBackHandler, FeedBackWeixinHandler
from handlers.download import DownloadHandler, DownloadTerminalHandler, DownloadSmsHandler, UploadTerminalHandler, DownloadManualHandler
from handlers.about import AboutHandler
from handlers.instruction import WebInsHandler, AndroidInsHandler, IOSInsHandler, SMSInsHandler, ManualInsHandler
from handlers.servicesterms import ServicesTermsHandler
from handlers.helper import HelperHandler 
from handlers.charge import ChargeHandler 
from handlers.clientdownload import ClientDownloadHandler 
from handlers.wapimg import WapImgHandler
from handlers.tinyurl import TinyURLHandler
from handlers.delegation import DelegationHandler
from handlers.checker import CheckTMobileHandler, CheckCNumHandler, CheckCNameHandler
from handlers.checker import CheckOperMobileHandler, CheckPassengerMobileHandler
from handlers.friendlink import FriendLinkHandler
from handlers.batch import BatchImportHandler
from handlers.batch import BatchDeleteHandler
from handlers.batch import BatchJHHandler
from handlers.batch import BatchSpeedlimitHandler
from handlers.operator import OperatorHandler
from handlers.region import RegionHandler, RegionDetailHandler
from handlers.corpregion import CorpRegionHandler
from handlers.bindregion import BindRegionHandler
from handlers.single import SingleHandler
from handlers.corpsingle import CorpSingleHandler, CorpSingleListHandler, CorpSingleDetailHandler
from handlers.bindsingle import BindSingleHandler
from handlers.online import OnlineHandler, OnlineDownloadHandler
from handlers.zfjsyncer import ZFJSyncerHandler
from handlers.ownerservice import OwnerserviceHandler
from handlers.mileagenotification import MileageNotificationHandler 

#znbc uweb handler
from handlers.passenger import PassengerHandler
from handlers.line import LineHandler
from handlers.information import InformationHandler
from handlers.bindline import LinesGetHandler, BindlineHandler

#znbc client handler
from handlers.clientcorpsearch import CorpSearchHandler
from handlers.clientcar import FocusCarHandler, UnbindCarHandler
from handlers.clientpush import PushHandler
from handlers.clientmap import MAPHandler
from handlers.clientbindmobile import ClientCaptchaHandler, BindMobileHandler
from handlers.clientsync import SyncHandler
from handlers.avatar import AvatarHandler
from handlers.upload import UploadHandler
from handlers.attendance import AttendanceHandler
from handlers.bind import YDWQBindHandler
from handlers.acc import ACCHandler
from handlers.masspoint import MassPointHandler 
from handlers.masspoint_basic import MassPointBasicHandler 
from handlers.masspoint_day import MassPointDayHandler 
from handlers.wspush import WSPushHandler

from handlers.test_wspush import WSPushTestHandler

# utils
from handlers.uwebhelper import GEHandler


class Application(tornado.web.Application):

    def __init__(self, debug=False):
        handlers = [
            # NOTE: the order is important, the first matched pattern is used!!!
            (r"/", MainHandler),
            (r"/index", MainHandler),
            (r"/login/*", LoginHandler),
            (r"/logintest/*", LoginTestHandler),
            (r"/checkupdate/ios/*", CheckUpdateIOSHandler),
            (r"/checkupdate/*", CheckUpdateAndroidHandler),
            (r"/captcha", CaptchaHandler),
            (r"/captchasms", CaptchaSmsHandler),
            (r"/captchaimage", CaptchaImageHandler),
            (r"/captchapsd", CaptchaPasswordHandler),
            (r"/logout/*", LogoutHandler),
            (r"/switchcar/(\S+)/*", SwitchCarHandler),
            (r"/wakeup/*", WakeupHandler),
            (r"/inclastinfo/corp/*", IncLastInfoCorpHandler),
            (r"/lastinfo/corp/*", LastInfoCorpHandler),
            (r"/lastinfo/*", LastInfoHandler),
            (r"/lastposition/*", LastPositionHandler),

            (r"/track/*", TrackHandler),
            (r"/download/track/*", TrackDownloadHandler),

            (r"/tracklq/*", TrackLQHandler),
            (r"/kqly/*", KQLYHandler),
            (r"/event/*", EventHandler),
            (r"/eventperiod/*", EventPeriodHandler),
            (r"/realtime/*", RealtimeHandler),
            (r"/defend/weixin/*", DefendWeixinHandler),
            (r"/defend/*", DefendHandler),
            (r"/defend/weixin/*", DefendWeixinHandler),
            (r"/acc/*", ACCHandler),
            (r"/terminal/*", TerminalHandler),

            (r"/statistic/single/*", StatisticSingleHandler),
            (r"/download/statistic/single/*", StatisticSingleDownloadHandler),

            (r"/mileage/single/*", MileageSingleHandler),
            (r"/download/mileage/single/*", MileageSingleDownloadHandler),

            (r"/statistic/*", StatisticHandler),
            (r"/download/statistic/*", StatisticDownloadHandler),
            (r"/mileage/*", MileageHandler),
            (r"/mileage/junior/*", MileageJuniorHandler),
            (r"/download/mileage/*", MileageDownloadHandler),

            (r"/terminal/corp/*", TerminalCorpHandler),
            # depreacted
            (r"/getcaptcha/*", GetCaptchaHandler),
            (r"/getcaptcha/corp/*", GetCaptchaCorpHandler),
            (r"/secgetcaptcha/*", SecGetCaptchaHandler),
            (r"/secgetcaptcha/corp/*", SecGetCaptchaCorpHandler),

            (r"/password/*", PasswordHandler),
            (r"/password/corp/*", PasswordCorpHandler),
            (r"/password/oper/*", PasswordOperHandler),
            (r"/profile/*", ProfileHandler),
            (r"/profile/corp/*", ProfileCorpHandler),
            (r"/profile/oper/*", ProfileOperHandler),
            (r"/smsoption/corp/*", SMSOptionCorpHandler),
            (r"/smsoption/*", SMSOptionHandler),
            (r"/alarmoption/*", AlarmOptionHandler),
            (r"/appsettings/*", AppSettingsHandler),
            (r"/unbind/*", UNBindHandler),
            (r"/share/*", ShareHandler),
            (r"/activity/*", ActivityHandler),
            (r"/mileagenotification/*", MileageNotificationHandler),

            # for YDWQ
            (r"/announcement/*", AnnouncementHandler),
            (r"/announcement/list/*", AnnouncementListHandler),
            (r"/activationcode/*", ActivationcodeHandler),
            (r"/activate/*", ActivateHandler),
            (r"/ydwq/activate/*", YDWQActivateHandler),
            (r"/ydwq/bind/*", YDWQBindHandler),
            (r"/upload/*", UploadHandler),


            (r"/about/*", AboutHandler),

            (r"/feedback/weixin/*", FeedBackWeixinHandler),
            (r"/feedback/*", FeedBackHandler),

            (r"/instruction/web/*", WebInsHandler),
            (r"/instruction/android/*", AndroidInsHandler),
            (r"/instruction/ios/*", IOSInsHandler),
            (r"/instruction/sms/*", SMSInsHandler),
            (r"/instruction/manual/*", ManualInsHandler),

            (r"/download/manual/*", DownloadManualHandler),
            (r"/download/online/*", OnlineDownloadHandler),
            (r"/downloadsms/*", DownloadSmsHandler),
            (r"/uploadterminalfile/*", UploadTerminalHandler),

            (r"/register/browser/*", RegisterBrowserHandler),


            # for terminal lua    
            (r"/upload/terminal/*", UploadTerminalHandler),
            (r"/download/terminal/*", DownloadTerminalHandler),

            (r"/servicesterms/*", ServicesTermsHandler),
            (r"/helper/*", HelperHandler),
            (r"/charge/*", ChargeHandler),
            (r"/clientdownload/*", ClientDownloadHandler),

            # for android 
            (r"/android/*", AndroidHandler),
            (r"/logintest/android/*", AndroidLoginTestHandler),
            (r"/logout/android/*", AndroidLogoutHandler),

            # for ios
            (r"/ios/*", IOSHandler),
            (r"/logintest/ios/*", IOSLoginTestHandler),
            (r"/logout/ios/*", IOSLogoutHandler),

            # depreacted
            (r"/register/*", RegisterHandler),
            (r"/secregister/*", SecRegisterHandler),
            (r"/reregister/*", ReRegisterHandler),
           
            #znbc client handler
            (r"/ios/corpsearch/*", CorpSearchHandler),
            (r"/ios/focuscar/*", FocusCarHandler),
            (r"/ios/abandoncar/*", UnbindCarHandler),
            (r"/ios/push/*", PushHandler),
            (r"/ios/map/*", MAPHandler),
            (r"/ios/captcha/*", ClientCaptchaHandler),
            (r"/ios/bindmobile/*", BindMobileHandler),
            (r"/ios/sync/*", SyncHandler),
            (r"/zfjsyncer/*", ZFJSyncerHandler),

            (r"/avatar/*", AvatarHandler),
            (r"/attendance/*", AttendanceHandler),

            # for wap
            (r"/wapimg/*", WapImgHandler),

            # tinyurl
            (r"/tl/(\S+)/*", TinyURLHandler),

            # a secret url for delegation: uid/tid/sim, sign is provided via
            # ?s=xxxx
            (r"/delegation/5Luj5a6i5pON5L2c/(.*)/(.*)/(.*)/(.*)/(.*)/*", DelegationHandler),
            
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
            (r"/batch/speedlimit/*", BatchSpeedlimitHandler),
            (r"/operator/*", OperatorHandler),
            (r"/region/*", RegionHandler),
            (r"/bindregion/*", BindRegionHandler),
            (r"/getregionevent/*", RegionDetailHandler),
            (r"/report/online/*", OnlineHandler),
            (r"/download/*", DownloadHandler),
            (r"/corpregion/*", CorpRegionHandler),


            (r"/bindsingle/*", BindSingleHandler),
            (r"/corpsingle/*", CorpSingleHandler),
            (r"/corpsingle/list/*", CorpSingleListHandler),
            (r"/corpsingle/detail/*", CorpSingleDetailHandler),
            (r"/single/*", SingleHandler),

            (r"/masspoint/*", MassPointHandler),
            (r"/masspoint/basic/*", MassPointBasicHandler),
            (r"/masspoint/day/*", MassPointDayHandler),


            (r"/test/*", EventHandler),


            (r"/masspoint/*", MassPointHandler),

            (r"/wspush/*", WSPushHandler),
            (r"/testwspush/*", WSPushTestHandler),


            #znbc server handler
            (r"/passenger/*", PassengerHandler),
            (r"/line/*", LineHandler),
            (r"/pushinfo/*", InformationHandler),
            (r"/getlines/*", LinesGetHandler),
            (r"/bindline/*", BindlineHandler),
            (r"/checkpassengermobile/(\d+)/*", CheckPassengerMobileHandler),
            (r"/ownerservice/*", OwnerserviceHandler),

            # utils
            (r"/ge/*", GEHandler),

            # handle the invalid url
            #(r".*", MainHandler),
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
            app_name="ACBUWEB",
            #xsrf_cookies=True,
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
        logging.error("Ctrl-C is  pressed.")
    except:
        logging.exception("[uweb] Exit Exception")
    finally:
        logging.warn("[uweb] shutdown...")
        shutdown(worker_pool, http_server)
        logging.warn("[uweb] stopped. Bye!")

if __name__ == "__main__":
    main()
