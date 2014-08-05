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
        res = []
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
            logging.info("[UWEB] LOCALGE return res:%s", res) 

            # LOCAL work well
            if res and res[0]['lat'] and res[0]['lon']:
                pass
            else:
                res = []
                lats = []
                lons = []
                for p in positions: 
                    longitude = p.split(',')[0] 
                    latitude = p.split(',')[1]
                    lons.append(float(longitude))
                    lats.append(float(latitude))

                clats, clons = lbmphelper.get_clocation_from_ge(lats, lons)
                logging.info("[UWEB] BAIDUGE return clats: %s, clons: %s", clats, clons) 
                for lat, lon in zip(clats, clons):
                    res.append({'lon':lon,
                                'lat':lat})   

            ##NOTE: If offset success, modify the DB 
            #if ret and ret[0]['lat'] and res[0]['lon']:
            #    for latlon, clatlon in zip(ret, res):
            #        if clatlon['lon'] and clatlon['lat']:
            #            self.db.execute("UPDATE T_LOCATION"
            #                            "  SET clongitude = %s,"
            #                            "      clatitude = %s"
            #                            "  WHERE longitude = %s"
            #                            "    AND latitude = %s",
            #                            clatlon['lon'],
            #                            clatlon['lat'],
            #                            latlon['lon'],
            #                            latlon['lat'])

            self.write_ret(status=status, dict_=dict(res=res)) 
        except Exception as e:
            logging.exception("[UWEB] GE request exception:%s",
                              e.args)
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)
