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
        request = {"homeMobileCountryCode":mcc, 
                   "homeMobileNetworkCode":mnc, 
                   "radio_type":"gsm", 
                   "cellTowers":
                    [ 
                     {"cellId":cid,
                      "locationAreaCode":lac, 
                      "homeMobileCountryCode":mcc, 
                      "homeMobileNetworkCode":mnc, 
                      "age": 0, 
                      "signalStrength": -60,
                      "timingAdvance": 5555
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
                response, content = self.http.request(ConfHelper.LBMP_CONF.le_full_path, HTTP.METHOD.POST, request)
                logging.info('[LE] response:\n %s, \ncontent:\n %s', response, content)
                json_data = json_decode(content)
                if json_data.get("location"):
                    ret.position.lat = int(json_data["location"]["lat"] * 3600000)
                    ret.position.lon = int(json_data["location"]["lng"] * 3600000)
                    ret.success = ErrorCode.SUCCESS 
                    ret.info = ErrorCode.ERROR_MESSAGE[ret.success]
                    logging.info("[LE] get lat=%s, lon=%s  through lac=%s, cid=%s", 
                                 ret.position.lat, ret.position.lon, data.lac, data.cid)
            except Exception as e:
                logging.exception("[LE] get latlon failed. Exception: %s", e.args)
            self.write(ret)
            IOLoop.instance().add_callback(self.finish)

        self.queue.put((LBMP.PRIORITY.LE, _on_finish))
