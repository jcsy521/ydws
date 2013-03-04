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
                response = self.send(ConfHelper.LBMP_CONF.gd_host, 
                                     ConfHelper.LBMP_CONF.gd_gv_url % (data.lon, data.lat, ConfHelper.LBMP_CONF.gd_key),
                                     None, HTTP.METHOD.GET)
                address = response.decode("GB2312")
                logging.info("[GV] response:%s", address)
                if len(address) > 5:
                    ret.address = address.rstrip()
                    ret.success = ErrorCode.SUCCESS 
                    ret.info = ErrorCode.ERROR_MESSAGE[ret.success]
                    logging.info("[GV] get address=%s through lat=%s, lon=%s",
                                 ret.address, data.lat, data.lon)
                else:
                    logging.error("[GV] get address failed. response:\n %s", address)
            except Exception as e:
                logging.exception("[GV] get address failed. Exception: %s", e.args)
            self.write(ret)
            IOLoop.instance().add_callback(self.finish)
            
        self.queue.put((LBMP.PRIORITY.GV, _on_finish))
