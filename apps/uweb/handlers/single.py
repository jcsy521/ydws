# -*- coding: utf-8 -*-

"""This module is designed for querying of single.
"""

import logging

import tornado.web

from utils.dotdict import DotDict
from helpers.queryhelper import QueryHelper
from constants import UWEB
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
            logging.exception("[UWEB] Get single data format illegal. cid: %s, Exception: %s",
                              self.current_user.cid, e.args)
            self.write_ret(status)
            return

        try:
            single = QueryHelper.get_single(single_id, self.db)
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
                    dct = {'latitude': latlon[0],
                           'longitude': latlon[1]}
                    polygon.append(dct)

                res = DotDict(single_id=single.single_id,
                              single_name=single.single_name,
                              single_shape=single.single_shape,
                              polygon=polygon)

            self.write_ret(status,
                           dict_=DotDict(res=res))
        except Exception as e:
            logging.exception("[UWEB] Get single failed.  cid: %s, Exception: %s",
                              self.current_user.cid, e.args)
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)
