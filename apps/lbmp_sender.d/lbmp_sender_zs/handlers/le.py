# -*- coding: utf-8 -*-

import logging
import re
import httplib

import tornado.web
from tornado.escape import json_decode, json_encode
from tornado.ioloop import IOLoop

from utils.dotdict import DotDict
from codes.errorcode import ErrorCode
from constants import LBMP, HTTP
from helpers.confhelper import ConfHelper

from lbmp.packet.composer.zsle_composer import ZsLeComposer
from lbmp.packet.parser.zsle_parser import ZsLeParser

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
                logging.info("[LE] Zsle response after parser:%s", zlp)
                if zlp.success == "000":
                     ret.position = zlp.get_position()
                else:
                    logging.info("[LE] Zsle request error:%s, google le started.", zlp.success)
                    logging.info('[LE] Google request:\n %s', request)
                    response = self.send(ConfHelper.LBMP_CONF.le_host, 
                                         ConfHelper.LBMP_CONF.le_url, 
                                         request,
                                         HTTP.METHOD.POST)
                    logging.info('[LE] Google response:\n %s', response.decode('utf8'))
                    json_data = json_decode(response)
                    if json_data.get("location"):
                        ret.position.lat = int(json_data["location"]["latitude"] * 3600000)
                        ret.position.lon = int(json_data["location"]["longitude"] * 3600000)
                        ret.success = ErrorCode.SUCCESS 
                        ret.info = ErrorCode.ERROR_MESSAGE[ret.success]
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
        conn = httplib.HTTPConnection("pinganbb.net", timeout=30)
        conn.request("POST", "/le", zs_request, headers)
        response = conn.getresponse()
        data = response.read()
        # logging.info("[LE] Zs response:%s", data)
        conn.close()
        return data
