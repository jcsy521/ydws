# -*- coding: utf-8 -*-

import logging
import base64 
from decimal import Decimal

import tornado.web
from tornado.escape import json_decode, json_encode
from tornado.ioloop import IOLoop

from codes.errorcode import ErrorCode
from utils.dotdict import DotDict
from constants import LBMP, HTTP
from helpers.confhelper import ConfHelper
from base import BaseHandler

class LocalGeHandler(BaseHandler):
    
    @tornado.web.removeslash
    @tornado.web.asynchronous
    def post(self):
        """Get the lat, lon and return clat, clon 
        @params: position, [{"lon":*,"lat":*}, {}, ...]
        @returns: ret = {status=status,
                         info=message,
                         position=[{"lat":degree * 3600000,
                                    "lon":degree * 3600000},
                                   {},...]
                        }
        """
        ret = dict(status=ErrorCode.LOCATION_OFFSET_FAILED,
                   info=ErrorCode.ERROR_MESSAGE[ErrorCode.LOCATION_OFFSET_FAILED],
                   position=[])
        try:
            data = DotDict(json_decode(self.request.body))
            logging.info('[LOCALGE] Request:\n %s', data)
        except Exception as e:
            logging.exception("[LOCALGE] Get latlng_offset failed. Exception: %s", e.args)
            self.write(ret)
            IOLoop.instance().add_callback(self.finish) 
            return

        def _on_finish():
            try:
                task = "lbmp"
                coords = task + "+"
                coords_list = []
                clons = []
                clats = []
                for point in data["position"]:
                    lat = float(point["lat"]) / 3600000
                    lon = float(point["lon"]) / 3600000
                    coords_list.append(str(lat))
                    coords_list.append(str(lon))
                coords += "+".join(coords_list)
                response, content = self.http.request(ConfHelper.LBMP_CONF.local_ge_multipoints_url  % (coords), HTTP.METHOD.GET)
                logging.info('[LOCALGE] response: %s, content: %s', response, content)
                if response['status'] == '200':
                    if content:
                        ret["status"] = ErrorCode.SUCCESS
                        ret["info"] = ErrorCode.ERROR_MESSAGE[ret["status"]]
                        content = content.split(" ")
                        if content[0] == task:
                            results = content[1:]
                            for i, result in enumerate(results):
                                if i % 2 == 0:
                                    clats.append(int(Decimal(result) * 3600000))
                                else:
                                    clons.append(int(Decimal(result) * 3600000))
                            ret["position"] = map(lambda plon, plat: dict(lon=plon, lat=plat),
                                                  clons,
                                                  clats)
                            logging.info("[LOCALGE] Get latlon_offset success.  ret: %s", ret)
                    else:
                        logging.exception("[LOCALGE] Get latlon_offset failed.  content: %s", content)
                else:
                    logging.exception("[LOCALGE] Get latlon_offset failed.  response: %s", response)
            except Exception as e:
                logging.exception("[LOCALGE] Get latlon_offset failed. Exception: %s", e.args)

            self.write(ret)
            IOLoop.instance().add_callback(self.finish)
             
        self.queue.put((LBMP.PRIORITY.GE, _on_finish))
