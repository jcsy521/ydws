# -*- coding: utf-8 -*-

import logging
import re

import tornado.web
from tornado.escape import json_decode, json_encode
from tornado.ioloop import IOLoop

from utils.dotdict import DotDict
from codes.errorcode import ErrorCode
from constants import LBMP, HTTP
from helpers.confhelper import ConfHelper

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
            logging.info('[LE] request:\n %s', data)
            request = self.composer(data.lac, data.cid, data.mcc, data.mnc)
        except Exception as e:
            logging.exception("[LE] get latlon failed. Exception: %s", e.args)
            self.write(ret)
            IOLoop.instance().add_callback(self.finish) 
            return

        def _on_finish():
            try:
                response = self.send(ConfHelper.LBMP_CONF.le_host, 
                                     ConfHelper.LBMP_CONF.le_url, 
                                     request,
                                     HTTP.METHOD.POST)
                logging.info('[LE] response:\n %s', response)
                json_data = json_decode(response)
                if json_data.get("location"):
                    ret.position.lat = int(json_data["location"]["latitude"] * 3600000)
                    ret.position.lon = int(json_data["location"]["longitude"] * 3600000)
                    ret.success = ErrorCode.SUCCESS 
                    ret.info = ErrorCode.ERROR_MESSAGE[ret.success]
                    logging.info("[LE] get lat=%s, lon=%s  through lac=%s, cid=%s", 
                                 ret.position.lat, ret.position.lon, data.lac, data.cid)
            except Exception as e:
                logging.exception("[LE] get latlon failed. Exception: %s", e.args)
            self.write(ret)
            IOLoop.instance().add_callback(self.finish)

        self.queue.put((LBMP.PRIORITY.LE, _on_finish))
