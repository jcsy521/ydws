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

class GvHandler(BaseHandler):

    @tornado.web.removeslash
    @tornado.web.asynchronous
    def post(self):
        """Get address through lat and lon.
        @params: lat, degree
                 lon, degree
        @returns: ret={success=status,
                       info=message,
                       address=address}

        """
        ret=DotDict(success=ErrorCode.LOCATION_NAME_NONE,
                    info=ErrorCode.ERROR_MESSAGE[ErrorCode.LOCATION_NAME_NONE],
                    address="")
        try:
            data = DotDict(json_decode(self.request.body))
            logging.info('[GV] request:\n %s', data)
        except Exception as e:
            logging.exception("[GV] get address failed. Exception: %s", e.args)
            self.write(ret)
            IOLoop.instance().add_callback(self.finish)
            return
             
        def _on_finish():
            try:
                response = self.send(ConfHelper.LBMP_CONF.gv_host, 
                                     ConfHelper.LBMP_CONF.gv_url % (data.lat, data.lon),
                                     None, HTTP.METHOD.GET)       
                logging.info("[GV] response:\n %s", "Too many words, DUMMY response instead.")
                if response:
                    json_data = json_decode(response)
                    if json_data['status'] == 0: # success 
                        logging.info("result: %s", json_data['result'])
                        ret.address = json_data['result']['formatted_address']
                        if len(json_data['result']['pois']) >= 1:
                            pois = json_data['result']['pois']
                            pois.sort(key=lambda item: int(item['distance']))
                            poi_name = pois[0]['name']
                            if poi_name:
                                ret.address += u"，" + poi_name + u'附近'
                        ret.success = ErrorCode.SUCCESS 
                        ret.info = ErrorCode.ERROR_MESSAGE[ret.success]
                        logging.info("[GV] get address=%s through lat=%s, lon=%s",
                                     ret.address, data.lat, data.lon)
                    else:
                        logging.error("[GV] get address failed. response:\n %s", response)
                else:
                    logging.error("[GV] get address failed. response:\n %s", response)
                    
            except Exception as e:
                logging.exception("[GV] get address failed. Exception: %s", e.args)
            self.write(ret)
            IOLoop.instance().add_callback(self.finish)
            
        self.queue.put((LBMP.PRIORITY.GV, _on_finish))
