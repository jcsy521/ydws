#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os.path
import site

TOP_DIR_ = os.path.abspath(os.path.join(__file__, "../../.."))
site.addsitedir(os.path.join(TOP_DIR_, "libs"))

import logging

import tornado.httpserver
import tornado.ioloop
import tornado.web
from tornado.options import define, options
define('port', type=int, default=7000)
define('conf', default=os.path.join(TOP_DIR_, "conf/global.conf"))
# deploy or debug
define('mode', default='deploy')
# use warning for deployment
try:
    #options['logging'].set('warning')
    options['logging'].set('info')
except:
    options.logging='warning'

from helpers.confhelper import ConfHelper
from db_.mysql import DBConnection
from utils.myredis import MyRedis

from utils.dotdict import DotDict

from handlers.main import MainHandler
from handlers.captcha import CaptchaHandler
from handlers.login import LoginHandler, LoginHistoryHandler
from handlers.logout import LogoutHandler
from handlers.administrator import AdministratorSearchHandler
from handlers.administrator import AdministratorListHandler
from handlers.administrator import AdministratorEditHandler
from handlers.administrator import AdministratorSelfEditHandler
from handlers.administrator import AdministratorCreateHandler
from handlers.administrator import AdministratorDeleteHandler
from handlers.privgroup import * 
from handlers.password import MyPasswordHandler, OtherPasswordHandler
from handlers.delegate import DelegationHandler, DelegationLogHandler
from handlers.business import * 
from handlers.ecbusiness import * 
from handlers.whitelist import WLSearchHandler, AddWLHandler, WhitelistBatchImportHandler, WhitelistBatchAddHandler 
from handlers.subscriber import SubscriberHandler, SubscriberDownloadHandler
from handlers.ecsubscriber import ECSubscriberHandler, ECSubscriberDownloadHandler
#from handlers.yearly import YearlyHandler, YearlyDownloadHandler
#from handlers.monthly import MonthlyHandler, MonthlyDownloadHandler
#from handlers.daily import DailyHandler, DailyDownloadHandler
from handlers.online import OnlineHandler, OnlineDownloadHandler
from handlers.individual import IndividualHandler, IndividualDownloadHandler
from handlers.enterprise import EnterpriseHandler, EnterpriseDownloadHandler
from handlers.total import TotalHandler, TotalDownloadHandler
from handlers.offline import OfflineHandler, OfflineDownloadHandler
from handlers.misc import *
from handlers.activity import ActivityHandler, ActivityListHandler
from handlers.apk import ApkHandler, ApkListHandler
from handlers.usertype import UserTypeHandler
from handlers.username import UsernameHandler
from handlers.resetpassword import ResetPasswordHandler 
from handlers.locationre import LocationSearchHandler, LocationSearchDownloadHandler
from handlers.bindlog import BindLogSearchHandler, BindLogDownloadHandler
from handlers.manuallog import ManualLogSearchHandler, ManualLogDownloadHandler
from handlers.notification import NotificationSearchHandler
from handlers.register import RegisterSearchHandler, RegisterClearHandler
from handlers.setting import SettingHandler
from handlers.ownerservice import OwnerServiceHandler, OwnerServiceDownloadHandler
# ajt
from handlers.whitelist_ajt import WhitelistAJTHandler, WhitelistAJTSearchHandler, WhitelistAJTBatchImportHandler,WhitelistAJTBatchAddHandler
from handlers.testsms import TestSMSHandler

class Application(tornado.web.Application):

    def __init__(self, debug=False):
        handlers = [
            # NOTE: the order is important, the first matched pattern is used!!!
            (r"/", MainHandler),
            (r"/login", LoginHandler),
            (r"/loginhistory", LoginHistoryHandler),
            (r"/captcha", CaptchaHandler),
            (r"/logout", LogoutHandler),

            # administrator management
            (r"/administrator/list/(\d+)/*", AdministratorListHandler),
            (r"/administrator/search/*", AdministratorSearchHandler),
            (r"/administrator/edit/(\d+)/*", AdministratorEditHandler),
            (r"/administrator/delete/(\d+)/*", AdministratorDeleteHandler),
            (r"/administrator/create/*", AdministratorCreateHandler),

            (r"/administrator/me/*", AdministratorSelfEditHandler),           
            (r"/administrator/password/me/*", MyPasswordHandler),
            (r"/administrator/password/other/*", OtherPasswordHandler),

            # privilege group
            (r"/privgroup/list/*", PrivGroupListHandler),
            (r"/privgroup/create/*", PrivGroupCreateHandler),
            (r"/privgroup/edit/(\d+)/*", PrivGroupEditHandler),
            (r"/privgroup/delete/(\d+)/*", PrivGroupDeleteHandler),

            # delegation
            (r"/delegation/*", DelegationHandler),
            (r"/delegation/log/*", DelegationLogHandler),

            # business 
            (r"/business/search/*", BusinessSearchHandler),
            (r"/business/create/*", BusinessCreateHandler),
            (r"/business/list/(\S+)/*", BusinessListHandler),
            (r"/business/edit/(\S+)/*", BusinessEditHandler), 
            (r"/business/delete/(\S+)/(\S+)/(\S+)/*", BusinessDeleteHandler),
            (r"/business/service/(\S+)/(\S+)/*", BusinessServiceHandler),
            
            # EC business
            (r"/ecbusiness/search/*", ECBusinessSearchHandler),
            (r"/ecbusiness/createec/*", ECBusinessCreateHandler),
            (r"/ecbusiness/addterminal/*", ECBusinessAddTerminalHandler),
            (r"/ecbusiness/list/(\S+)/*", ECBusinessListHandler),
            (r"/ecbusiness/edit/(\S+)/*", ECBusinessEditHandler),
            (r"/ecbusiness/delete/(\S+)/*", ECBusinessDeleteHandler),


            # termianl query
            (r"/bindlog/*", BindLogSearchHandler),
            (r"/manuallog/*", ManualLogSearchHandler),
			(r"/notification/*", NotificationSearchHandler),
			(r"/register/*", RegisterSearchHandler),
			(r"/register/delete/*", RegisterClearHandler),
			(r"/setting/*", SettingHandler),
            (r"/location/*", LocationSearchHandler),
            (r"/ownerservice/*", OwnerServiceHandler),
            (r"/testsms/*", TestSMSHandler),
            

            # for ajt
            (r"/whitelist_ajt/*", WhitelistAJTHandler),
            (r"/whitelist_ajt/search/*", WhitelistAJTSearchHandler),
            (r"/whitelist_ajt/batch/import/*", WhitelistAJTBatchImportHandler),
            (r"/whitelist_ajt/batch/add/*", WhitelistAJTBatchAddHandler),


            # whitelist search add update
            (r"/whitelist_search",WLSearchHandler),
            (r"/whitelist",AddWLHandler),
            (r"/whitelist/batch/import/*", WhitelistBatchImportHandler),
            (r"/whitelist/batch/add/*", WhitelistBatchAddHandler),

            # misc
            (r"/administrator/checkloginname/(.*)/*", AdministratorLoginnameHandler),
            (r"/administrator/checkprivilegegroupname/(.*)/*", PrivilegeGroupNameHandler),
            (r"/corplist/*", CorpListHandler),
            (r"/checkecmobile/(\d+)/*", CheckECMobileHandler),
            (r"/checkecname/(\S+)/*", CheckECNameHandler),
            (r"/checktmobile/(\d+)/*", CheckTMobileHandler),
            (r"/checkcnum/(\S+)/*", CheckCNumHandler),
            (r"/privileges/(\d+)/*", PrivilegeSetHandler),


            # statistic report
            (r"/report/subscriber/*", SubscriberHandler),
            (r"/report/ecsubscriber/*", ECSubscriberHandler),
            #(r"/report/yearly/*", YearlyHandler),
            #(r"/report/monthly/*", MonthlyHandler),
            #(r"/report/daily/*", DailyHandler),
            #(r"/report/online/*", OnlineHandler),
            
            # new statistic report
            (r"/report/individual/*", IndividualHandler),
            (r"/report/enterprise/*", EnterpriseHandler),
            (r"/report/total/*", TotalHandler),
            (r"/report/offline/*", OfflineHandler),

            # download the report
            (r"/download/subscriber/(.*)/*", SubscriberDownloadHandler),
            (r"/download/ecsubscriber/(.*)/*", ECSubscriberDownloadHandler),
            #(r"/download/yearly/(.*)/*", YearlyDownloadHandler),
            #(r"/download/monthly/(.*)/*", MonthlyDownloadHandler),
            #(r"/download/daily/(.*)/*", DailyDownloadHandler),
            #(r"/download/online/(.*)/*", OnlineDownloadHandler),

            (r"/download/individual/(.*)/*", IndividualDownloadHandler),
            (r"/download/enterprise/(.*)/*", EnterpriseDownloadHandler),
            (r"/download/total/(.*)/*", TotalDownloadHandler),
            (r"/download/offline/(.*)/*", OfflineDownloadHandler),
            
            (r"/download/business/search/(.*)/*", BusinessSearchDownloadHandler),
            (r"/download/bindlog/(.*)/*", BindLogDownloadHandler),
            (r"/download/manuallog/(.*)/*", ManualLogDownloadHandler),
	        (r"/download/location/(.*)/*", LocationSearchDownloadHandler),
            (r"/download/ownerservice/(.*)/*", OwnerServiceDownloadHandler), 

            (r"/activity/*", ActivityHandler),
            (r"/activity/list/*", ActivityListHandler),
            (r"/apk/*", ApkHandler),
            (r"/apk/list/*", ApkListHandler),

            (r"/usertype/*", UserTypeHandler),
            (r"/username/*", UsernameHandler),
            (r"/resetpassword/*", ResetPasswordHandler),
            
            ] 

        settings = dict(
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            cookie_secret="s8g1gVxKOiQoZptLRi2nSuXmiK2ThYJJBSHIUHnqoUw=",
            login_url="/login",
            #debug=debug,
            app_name="ACBADMIN",
        )

        tornado.web.Application.__init__(self, handlers, **settings)

        self.db = DBConnection().db
        self.redis = MyRedis()


def shutdown(server):
    try:
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
        http_server = tornado.httpserver.HTTPServer(Application(debug=debug_mode), xheaders=True)
        http_server.listen(options.port)
        logging.warn("[admin] running on: localhost:%d", options.port)
        tornado.ioloop.IOLoop.instance().start()
    except KeyboardInterrupt: # todo: SystemExit?
        logging.error("Ctrl-C is pressed.")
    except:
        logging.exception("[admin] Exit Exception")
    finally:
        logging.warn("[admin] shutdown...")
        if http_server is not None:
            shutdown(http_server)
        logging.warn("[admin] stopped. Bye!")


if __name__ == "__main__":
    main()
