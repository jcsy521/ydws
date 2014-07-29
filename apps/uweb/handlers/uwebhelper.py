# -*- coding: utf-8 -*-

import hashlib
import hmac
import logging

from tornado.escape import json_encode
import tornado.web

from codes.errorcode import ErrorCode
from base import BaseHandler, authenticated
from codes.errorcode import ErrorCode
from helpers import lbmphelper
from utils.dotdict import DotDict


class GEHandler(BaseHandler):
    
    @authenticated
    @tornado.web.removeslash
    def get(self):
        status = ErrorCode.SUCCESS
        try:
            positions_str = self.get_argument('positions')
            positions = positions_str.split(';')
            logging.info("[UWEB] GE request positions_str:%s, positions:%s",
                         positions_str, positions)
                         
            ret = [] 
            for p in positions: 
                longitude = p.split(',')[0] 
                latitude = p.split(',')[1] 
                ret.append(dict(lon=longitude, lat=latitude)) 

            res = lbmphelper.get_clocation_from_localge(ret) 
            logging.info("[UWEB] GE return res:%s", res) 
            self.write_ret(status=status, dict_=dict(res=res)) 

        except Exception as e:
            logging.exception("[UWEB] GE request exception:%s",
                              e.args)
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)
