# -*- coding: utf-8 -*-

import logging
import re

import tornado.web
from tornado.escape import json_decode, json_encode
from tornado.ioloop import IOLoop

from codes.errorcode import ErrorCode
from utils.dotdict import DotDict
from constants import LBMP
from helpers.confhelper import ConfHelper
from lbmp.packet.composer.subscription_composer import SubscriptionComposer
from lbmp.packet.parser.subscription_parser import SubscriptionParser
from base import BaseHandler

class SubscriptionHandler(BaseHandler):
    
    @tornado.web.removeslash
    @tornado.web.asynchronous
    def post(self):
        ret=DotDict(success=ErrorCode.FAILED,
                    info="")
        try:

#            args = dict(id="ZSCLGZ",
#                        pwd="ZSCLGZ20120920",
#                        serviceid="ZSCLGZ",
#                        appName="ACB",
#                        area="0760")

            args = dict(id="zsds20120224",
                        pwd="zsds20120224",
                        serviceid="zsds",
                        appName=u"中山的士",
                        area="0760")
            data = dict(json_decode(self.request.body))
            status = ErrorCode.SUCCESS
            args['phoneNum'] = data['sim']
            args['action'] = data['action']
        except Exception as e:
            logging.exception("[SUBSCRIPTION] process failed. Exception: %s", e.args)
            self.write(ret)
            IOLoop.instance().add_callback(self.finish)
            return
             
        def _on_finish():
            try:
                sc = SubscriptionComposer(args)
                logging.debug("Subscription request:\n%s", sc.get_request())
                response = self.send(ConfHelper.LBMP_CONF.zs_host,
                                     ConfHelper.LBMP_CONF.zs_subscription_url,
                                     sc.get_request())
                logging.debug("Subscription response:\n%s", response.decode('utf-8'))
                sp = SubscriptionParser(response)
                ret.success = sp.success
                ret.info = sp.info
            except Exception as e:
                logging.exception("Subscription error: %s", e.args)
            self.write(ret)
            IOLoop.instance().add_callback(self.finish)

        self.queue.put((LBMP.PRIORITY.SUBSCRIPTION, _on_finish))
