# -*- coding: utf-8 -*-

import logging
import re

import tornado.web
from tornado.escape import json_decode, json_encode
from tornado.ioloop import IOLoop

from utils.dotdict import DotDict
from codes.errorcode import ErrorCode
from constants import LBMP 
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
            status = ErrorCode.SUCCESS
            url = ConfHelper.LBMP_CONF.gv_url_baidu % (data.lat, data.lon)
        except Exception as e:
            logging.exception("[GV] get address failed. Exception: %s", e.args)
            self.write(ret)
            IOLoop.instance().add_callback(self.finish)
            return
             
        def _on_finish():
            try:
                response, content = self.http.request(url)       
                logging.info("[GV] response:\n %s", "Too many words, DUMMY response instead.")
                json_data = json_decode(content)
                if json_data['status'] == 'OK':
                    #ret.address = json_data['results'][0]['formatted_address']
                    ret.address = json_data['result']['formatted_address']
                    ret.success = ErrorCode.SUCCESS 
                    logging.info("[GV] get address=%s through lat=%s, lon=%s",
                                 ret.address, data.lat, data.lon)
            except Exception as e:
                logging.exception("[GV] get address failed. Exception: %s", e.args)
            self.write(ret)
            IOLoop.instance().add_callback(self.finish)
            
        self.queue.put((LBMP.PRIORITY.GV, _on_finish))
