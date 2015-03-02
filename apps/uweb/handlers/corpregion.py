# -*- coding: utf-8 -*-

"""This module is designed for single.
"""

import logging

import tornado.web
from tornado.escape import json_decode

from utils.dotdict import DotDict
from constants import UWEB, LIMIT
from utils.public import add_region
from helpers.queryhelper import QueryHelper
from codes.errorcode import ErrorCode
from base import BaseHandler, authenticated


class CorpRegionHandler(BaseHandler):

    """Handle the regions of corp.

    :url /corpregion
    """

    @authenticated
    @tornado.web.removeslash
    def get(self):
        """ Get regions by cid"""
        status = ErrorCode.SUCCESS
        try:
            cid = self.current_user.cid
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            logging.exception("[UWEB] Get region data format illegal. uid: %s, Exception: %s",
                              self.current_user.uid, e.args)
            self.write_ret(status)
            return

        try:
            res = []
            regions = QueryHelper.get_regions_by_cid(cid, self.db)
            for region in regions:
                if region.region_shape == UWEB.REGION_SHAPE.CIRCLE:
                    r = DotDict(region_id=region.region_id,
                                region_name=region.region_name,
                                region_shape=region.region_shape,
                                circle=DotDict(latitude=region.latitude,
                                               longitude=region.longitude,
                                               radius=region.radius),
                                )
                elif region.region_shape == UWEB.REGION_SHAPE.POLYGON:
                    polygon = []
                    points = region.points
                    point_lst = points.split(':')
                    for point in point_lst:
                        latlon = point.split(',')
                        dct = {'latitude': latlon[0],
                               'longitude': latlon[1]}
                        polygon.append(dct)

                    r = DotDict(region_id=region.region_id,
                                region_name=region.region_name,
                                region_shape=region.region_shape,
                                polygon=polygon)

                res.append(r)
            self.write_ret(status,
                           dict_=DotDict(res=res))
        except Exception as e:
            logging.exception("[UWEB] Get regions failed. cid: %s, Exception: %s",
                              cid, e.args)
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)

    @authenticated
    @tornado.web.removeslash
    def post(self):
        """Create a new corp region.
        """
        try:
            data = DotDict(json_decode(self.request.body))
            logging.info("[UWEB] add region request: %s, cid: %s",
                         data, self.current_user.cid)
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            logging.exception("[UWEB] Invalid data format. body:%s, Exception: %s",
                              self.request.body, e.args)
            self.write_ret(status)
            return

        try:
            # NOTE: check numbers of regions of the corp.
            regions = QueryHelper.get_regions_by_cid(
                self.current_user.cid, self.db)
            if len(regions) > LIMIT.REGION - 1:
                self.write_ret(ErrorCode.REGION_ADDITION_EXCESS)
                return

            status = ErrorCode.SUCCESS
            rid = -1
            region_name = data.region_name
            region_shape = int(data.region_shape)
            if region_shape == UWEB.REGION_SHAPE.CIRCLE:
                circle = DotDict(data.circle)
                longitude = circle.longitude
                latitude = circle.latitude
                radius = circle.radius
                # create new region
                region_info = dict(region_name=region_name,
                                   longitude=longitude,
                                   latitude=latitude,
                                   radius=radius,
                                   shape=region_shape,
                                   cid=self.current_user.cid,)
                rid = add_region(region_info, self.db, self.redis)
            elif region_shape == UWEB.REGION_SHAPE.POLYGON:
                polygon = data.polygon
                points_lst = []
                points = ''
                for p in polygon:
                    tmp = ','.join([str(p['latitude']), str(p['longitude'])])
                    points += tmp
                    points_lst.append(tmp)
                points = ':'.join(points_lst)
                region_info = dict(region_name=region_name,
                                   points=points,
                                   shape=region_shape,
                                   cid=self.current_user.cid,)
                rid = add_region(region_info, self.db, self.redis)
            else:
                logging.error("[UWEB] Add region failed, unknown region_shape: %s, uid: %s",
                              region_shape, self.current_user.uid)

            self.write_ret(status,
                           dict_=DotDict(rid=rid))
        except Exception as e:
            logging.exception("[UWEB] Create region failed. cid: %s, Exception: %s",
                              self.current_user.cid, e.args)
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)
