# -*- coding: utf-8 -*-

import logging
import base64

import tornado.web
from tornado.escape import json_decode, json_encode
from tornado.ioloop import IOLoop

from codes.errorcode import ErrorCode
from utils.dotdict import DotDict
from constants import LBMP, HTTP
from helpers.confhelper import ConfHelper
from base import BaseHandler

class GeHandler(BaseHandler):
    
    @tornado.web.removeslash
    @tornado.web.asynchronous
    def post(self):
        """Get the lat, lon and return clat, clon 
        @params: lat, degree * 3600000 
                 lon, degree * 3600000
        @returns: ret = {success=status,
                         info=message,
                         position={clat=degree * 3600000,
                                   clon=degree * 3600000}
                        }
        """
        ret=DotDict(success=ErrorCode.LOCATION_OFFSET_FAILED,
                    info=ErrorCode.ERROR_MESSAGE[ErrorCode.LOCATION_OFFSET_FAILED],
                    position=DotDict(clat=0,
                                     clon=0))
        try:
            data = DotDict(json_decode(self.request.body))
            logging.info('[GE] request:\n %s', data)
        except Exception as e:
            logging.exception("[GE] get latlng_offset failed. Exception: %s", e.args)
            self.write(ret)
            IOLoop.instance().add_callback(self.finish) 
            return
             
        def _on_finish():
            try:
                response = self.send(ConfHelper.LBMP_CONF.ge_host,
                                     ConfHelper.LBMP_CONF.ge_url % (data.lat/3600000.0, data.lon/3600000.0),
                                     None, 
                                     HTTP.METHOD.GET)
                # NOTE: the response may be 
                # {"error":0,"x":"MTEzLjM5Njg3ODY3ODcx","y":"MjIuNTE0NjQ1MDk0NzE="}  or {'error':2,'x':'MA==','y':'MA=='} 
                # so here change the ' to "
                response = response.replace("'",'"')
                logging.info('[GE] response:\n %s', response)
                if response:
                    json_data = json_decode(response)
                    if json_data['error'] == 0:
                        lon = base64.b64decode(json_data['x'])
                        lat = base64.b64decode(json_data['y'])
                        ret.position.clat = int(float(lat) * 3600000)
                        ret.position.clon = int(float(lon) * 3600000)
                        logging.info("[GE] get clat=%s, clon=%s through lat=%s, lon=%s", 
                                        lat, lon, data.lat, data.lon)
                        ret.success = ErrorCode.SUCCESS 
                        ret.info = ErrorCode.ERROR_MESSAGE[ret.success]
                    else:
                        logging.error("[GV] get latlon_offset failed. response:\n %s", response)
                else:
                    logging.error("[GV] get latlon_offset failed. response:\n %s", response)

            except Exception as e:
                logging.exception("[GE] get latlon_offset failed. Exception: %s", e.args)

            self.write(ret)
            IOLoop.instance().add_callback(self.finish)

        self.queue.put((LBMP.PRIORITY.GE, _on_finish))
