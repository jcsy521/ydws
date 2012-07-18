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
options['logging'].set('warning')

from helpers.confhelper import ConfHelper
from db_.mysql import DBConnection
#from db_.mongodb import MongoDBConnection
#from db_.exceptions import MongoDBException
from utils.mymemcached import MyMemcached

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

from handlers.privgroup import PrivGroupListHandler
from handlers.privgroup import PrivGroupEditHandler
from handlers.privgroup import PrivGroupCreateHandler
from handlers.privgroup import PrivGroupDeleteHandler

from handlers.password import MyPasswordHandler, OtherPasswordHandler

from handlers.delegate import DelegationHandler, DelegationLogHandler

from handlers.user import UserHandler, UserDownloadHandler

from handlers.subscriber import SubscriberHandler, SubscriberDownloadHandler
#from handlers.location import LocationHandler, LocationDownloadHandler
from handlers.subscription import SubscriptionHandler, SubscriptionDownloadHandler
from handlers.business import BusinessHandler, BusinessDownloadHandler
from handlers.daily import DailyHandler, DailyDownloadHandler
from handlers.monthly import MonthlyHandler, MonthlyDownloadHandler
from handlers.group import GroupHandler, GroupDownloadHandler
#from handlers.sms import SMSHandler, SMSDownloadHandler


from handlers.misc import *


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

            (r"/delegation/*", DelegationHandler),
            (r"/delegation/log/*", DelegationLogHandler),

            # misc
            (r"/administrator/checkloginname/(.*)/*", AdministratorLoginnameHandler),
            (r"/administrator/checkprivilegegroupname/(.*)/*", PrivilegeGroupNameHandler),
            #(r"/administrator/(\d+)/status/*", AdministratorStatusHandler),
            #(r"/administrator/(\d+)/area/*", AreaPrivilegeHandler),
            #(r"/province/(\d+)/city/(\d+)/group/*", CityHandler),
            #(r"/province/(\d+)/city/*", ProvinceHandler),
            #(r"/province/*", ProvinceListHandler),
            (r"/user/mobile/(\d+)/*", UserInfoHandler),
            (r"/monitor/(\d+)/(\d+)/*", MonitorHandler),
            (r"/groups/*", GroupListHandler),
            (r"/privileges/(\d+)/*", PrivilegeSetHandler),

            # subscription log query
            #(r"/subscription/log/*", SubscriptionHandler),

            # user query
            (r"/user/search/*", UserHandler),
            (r"/user/subscription/*", SubscriptionHandler),
            (r"/download/user/(.*)/*", UserDownloadHandler),
            (r"/download/subscription/(.*)/*", SubscriptionDownloadHandler),

            # statistic report
            (r"/report/group/*", GroupHandler),
            (r"/report/subscriber/*", SubscriberHandler),
            #(r"/report/location/*", LocationHandler),
            (r"/report/monthly/*", MonthlyHandler),
            (r"/report/daily/*", DailyHandler),
            (r"/report/business/*", BusinessHandler),
            #(r"/report/sms/*", SMSHandler),

            # download the report
            #(r"/download/subscription/(.*)/*", SubscriptionDownloadHandler),
            (r"/download/subscriber/(.*)/*", SubscriberDownloadHandler),
            #(r"/download/location/(.*)/*", LocationDownloadHandler),
            (r"/download/monthly/(.*)/*", MonthlyDownloadHandler),
            (r"/download/daily/(.*)/*", DailyDownloadHandler),
            (r"/download/business/(.*)/*", BusinessDownloadHandler),
            (r"/download/group/(.*)/*", GroupDownloadHandler),
            #(r"/download/sms/(.*)/*", SMSDownloadHandler),
        ]

        settings = dict(
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            cookie_secret="s8g1gVxKOiQoZptLRi2nSuXmiK2ThYJJBSHIUHnqoUw=",
            login_url="/login",
            debug=debug,
            app_name="APPADMIN",
        )

        tornado.web.Application.__init__(self, handlers, **settings)

        self.db = DBConnection().db
        self.memcached = MyMemcached()
        #try:
        #    self.mongodb = MongoDBConnection().db
        #except MongoDBException as e:
        #    logging.error("Error: %s", e.args[0])


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
