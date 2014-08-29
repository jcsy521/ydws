# -*- coding: utf-8 -*-

import logging

import tornado.web
from tornado.escape import json_encode, json_decode

from utils.dotdict import DotDict
from utils.misc import DUMMY_IDS, str_to_list, get_region_status_key
from utils.checker import check_sql_injection
from constants import UWEB, LIMIT
from codes.errorcode import ErrorCode
from base import BaseHandler, authenticated


class SingleHandler(BaseHandler):

    @authenticated
    @tornado.web.removeslash
    def get(self):
        """Get the detail of a single. 
        """ 
        status = ErrorCode.SUCCESS
        try:
            single_id = self.get_argument('single_id')
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            logging.exception("[UWEB] cid: %s get single data format illegal. Exception: %s", 
                              self.current_user.cid, e.args) 
            self.write_ret(status)
            return
        
        try:
            single = self.db.get("SELECT id AS single_id, name AS single_name, longitude, latitude,"
                                 "  radius, points, shape AS single_shape"
                                 "  FROM T_SINGLE"
                                 "  WHERE id = %s",
                                 single_id)
            if not single:
                status = ErrorCode.SINGLE_NOT_EXISTED
                self.write_ret(status)
                return

            if single.single_shape == UWEB.REGION_SHAPE.CIRCLE:
                res = DotDict(single_id=single.single_id,
                            single_name=single.single_name,
                            single_shape=single.single_shape,
                            circle=DotDict(latitude=single.latitude,
                                           longitude=single.longitude,
                                           radius=single.radius),
                            )
            elif single.single_shape == UWEB.REGION_SHAPE.POLYGON:
                polygon = []
                points = single.points
                point_lst = points.split(':')
                for point in point_lst:
                    latlon = point.split(',')
                    dct = {'latitude':latlon[0],
                           'longitude':latlon[1]}
                    polygon.append(dct)
                
                res = DotDict(single_id=single.single_id,
                              single_name=single.single_name,
                              single_shape=single.single_shape,
                              polygon=polygon)
 
            self.write_ret(status,
                           dict_=DotDict(res=res))
        except Exception as e:
            logging.exception("[UWEB] cid: %s get single failed. Exception: %s", 
                              self.current_user.cid, e.args) 
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)
       
