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

from lbmp.packet.parser.ge_parser import GdGeParser

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
                response = self.send(ConfHelper.LBMP_CONF.gd_host,
                                     ConfHelper.LBMP_CONF.gd_ge_url % (float(data.lon)/3600000.0, 
                                                                       float(data.lat)/3600000.0, 
                                                                       ConfHelper.LBMP_CONF.gd_key),
                                     None, 
                                     HTTP.METHOD.GET)
                response = response.decode("GB2312")
                logging.info('[GE] response:\n %s', response)
                ggp = GdGeParser(response)
                if ggp.success == ErrorCode.SUCCESS: 
                    position = ggp.get_position()
                    ret.position.clat = int(float(position['clat']) * 3600000)
                    ret.position.clon = int(float(position['clon']) * 3600000)
                    logging.info("[GE] get clat=%s, clon=%s through lat=%s, lon=%s", 
                                       ret.position.clat, ret.position.clon, data.lat, data.lon)
                    ret.success = ErrorCode.SUCCESS 
                    ret.info = ErrorCode.ERROR_MESSAGE[ret.success]
                else:
                    ret.success = ggp.success
                    ret.info = ggp.info
                    logging.error("[GE] Get ge info error:%s, errorcode:%s", ret.info, ret.success)
            except Exception as e:
                logging.exception("[GE] get latlon_offset failed. Exception: %s", e.args)

            self.write(ret)
            IOLoop.instance().add_callback(self.finish)

        self.queue.put((LBMP.PRIORITY.GE, _on_finish))
