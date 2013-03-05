# -*- coding: utf-8 -*-

import logging
import re
import httplib
import time

import tornado.web
from tornado.escape import json_decode, json_encode
from tornado.ioloop import IOLoop
from functools import partial

from utils.dotdict import DotDict
from codes.errorcode import ErrorCode
from constants import LBMP, HTTP
from helpers.confhelper import ConfHelper

from lbmp.packet.composer.zsle_composer import ZsLeComposer
from lbmp.packet.parser.zsle_parser import ZsLeParser
from lbmp.packet.composer.subscription_composer import SubscriptionComposer
from lbmp.packet.parser.subscription_parser import SubscriptionParser

from base import BaseHandler

class LeHandler(BaseHandler):

    def composer(self, lac, cid, mcc=460, mnc=0):
        """Compose a message for goole to get latitude and lontitude through
        cellid information.
        """
        request = {"version":"1.1.0", 
                   "host":"maps.google.com", 
                   "home_mobile_country_code":mcc, 
                   "home_mobile_network_code":mnc, 
                   "address_language":"zh_CN", 
                   "radio_type":"gsm", 
                   "request_address":True, 
                   "cell_towers":
                    [ 
                     {"cell_id":cid,
                      "location_area_code":lac, 
                      "mobile_country_code":mcc
                     }, 
                    ] 
                  }
        return json_encode(request)
    
    @tornado.web.removeslash
    @tornado.web.asynchronous
    def post(self):
        """Get lat, lng throgh cellid information. 
        @params: lac, local area code 
                 cid, cellid code 
                 mcc, home mobile country code
                 mnc, home mobile network code
        @returns: ret = {success=status,
                         info=message,
                         position={lat=degree * 3600000,
                                   lon=degree * 3600000}
                        }
        """
        ret = DotDict(success=ErrorCode.LOCATION_CELLID_FAILED,
                      info=ErrorCode.ERROR_MESSAGE[ErrorCode.LOCATION_CELLID_FAILED],
                      position=DotDict(lat=0,
                                       lon=0))
        try:
            data = DotDict(json_decode(self.request.body))
            logging.info("[LE] Request args:%s", data)
            request = self.composer(data.lac, data.cid, data.mcc, data.mnc)
        except Exception as e:
            logging.exception("[LE] Get latlon failed. Exception: %s", e.args)
            self.write(ret)
            IOLoop.instance().add_callback(self.finish) 
            return

        def _on_finish():
            try:
                zs_response = self.zsle_request(data['sim'])
                zlp = ZsLeParser(zs_response.replace('GBK', 'UTF-8'))
                if zlp.success == "0":
                     ret.success = ErrorCode.SUCCESS
                     ret.position = zlp.get_position()
                     ret.info = ErrorCode.ERROR_MESSAGE[ret.success]
                     logging.info("[LE] Zsle response position: %s, sim:%s", ret.position, data['sim'])
                else:
                    if zlp.success == "9999228":
                        callback = partial(self.re_subscription, data['sim'])
                        IOLoop.instance().add_timeout(int(time.time()) + 5, callback)
                    logging.info("[LE] Zsle request failed, errorcode: %s, info: %s",
                                 zlp.success, zlp.info)
                    # logging.info('[LE] Google request:\n %s', request)
                    # response = self.send(ConfHelper.LBMP_CONF.le_host, 
                    #                      ConfHelper.LBMP_CONF.le_url, 
                    #                      request,
                    #                      HTTP.METHOD.POST)
                    # logging.info('[LE] Google response:\n %s', response.decode('utf8'))
                    # json_data = json_decode(response)
                    # if json_data.get("location"):
                    #     ret.position.lat = int(json_data["location"]["latitude"] * 3600000)
                    #     ret.position.lon = int(json_data["location"]["longitude"] * 3600000)
                    #     ret.success = ErrorCode.SUCCESS 
                    #     ret.info = ErrorCode.ERROR_MESSAGE[ret.success]
            except Exception as e:
                logging.exception("[LE] Get latlon failed. Exception: %s", e.args)
            self.write(ret)
            IOLoop.instance().add_callback(self.finish)

        self.queue.put((LBMP.PRIORITY.LE, _on_finish))

    def zsle_request(self, sim):
        args = DotDict(simcard=sim)
        zs_request = ZsLeComposer(args).get_request()
        logging.info("[LE] Zs request:%s", zs_request)
        headers = {"Content-type": "application/xml; charset=utf-8"}
        conn = httplib.HTTPConnection(ConfHelper.LBMP_CONF.zs_host, timeout=30)
        conn.request("POST", ConfHelper.LBMP_CONF.zs_le_url, zs_request, headers)
        response = conn.getresponse()
        data = response.read()
        # logging.info("[LE] Zs response:%s", data)
        conn.close()
        return data

    def re_subscription(self, sim):
        logging.info("[LBMP] Terminal: %s not reply sms, Re_subscription it.", sim)
        args = dict(id="ZSCLGZ",
                    pwd="ZSCLGZ20120920",
                    serviceid="ZSCLGZ",
                    appName="ACB",
                    area="0760")
        args['phoneNum'] = sim
        args['action'] = "D" 
        sc = SubscriptionComposer(args)
        response = self.send(ConfHelper.LBMP_CONF.zs_host,
                             ConfHelper.LBMP_CONF.zs_subscription_url,
                             sc.get_request())
        sp = SubscriptionParser(response)
        if sp.success == '000':
            logging.info("[LBMP] Cancel Subscription mobile: %s success!", sim)
            logging.info("[LBMP] Re_Subscription mobile: %s start...", sim)
            args['action'] = "A"
            sc = SubscriptionComposer(args)
            response = self.send(ConfHelper.LBMP_CONF.zs_host,
                                 ConfHelper.LBMP_CONF.zs_subscription_url,
                                 sc.get_request())
            sp = SubscriptionParser(response)
            if sp.success == '000':
                logging.info("[LBMP] Re_Subscription mobile: %s success!", sim)
            else:
                logging.info("[LBMP] Re_Subscription mobile: %s faild!", sim)
        else:
            logging.info("[LBMP] Cancel Subscription mobile: %s faild!", sim)
