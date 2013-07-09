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
                    position=DotDict(clats=[],
                                     clons=[]))
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
                # part new: offset multi-points
                if len(data.lats) != len(data.lons):
                    logging.error("Invalid data. len(lats)=%s, len(lons)=%s, lats: %s, lons: %s", 
                                  len(data.lats), len(data.lons), data.lats, data.lons)

                latlons = zip(data.lats, data.lons)

                lats = []
                lons = []

                clats = []
                clons = []

                for lat, lon in latlons:
                    lats.append(lat/3600000.0)
                    lons.append(lon/3600000.0)
                
                lats_s = ','.join([repr(lat) for lat in lats])
                lons_s = ','.join([repr(lon) for lon in lons])
                    
                response, content = self.http.request(ConfHelper.LBMP_CONF.ge_multipoints_url  % (lats_s, lons_s), HTTP.METHOD.GET)

                logging.info('[GE] response:\n %s, \ncontent:\n %s', response, content)
                if response['status'] == '200':
                    if content:
                        # NOTE: the content may be
                        # [{"error":0,"x":"MTEzLjM5Njg3ODY3ODcx","y":"MjIuNTE0NjQ1MDk0NzE="}]
                        # or [{'error':2,'x':'MA==','y':'MA=='}]
                        # so here change ' to "
                        content = content.replace("'",'"')
                        ret.success = ErrorCode.SUCCESS 
                        ret.info = ErrorCode.ERROR_MESSAGE[ret.success]
                        json_datas = json_decode(content)
                        for json_data in json_datas: 
                            if json_data['error'] == 0:
                                lon = base64.b64decode(json_data['x'])
                                lat = base64.b64decode(json_data['y'])
                                clats.append(int(Decimal(lat) * 3600000))
                                clons.append(int(Decimal(lon) * 3600000))
                            else: 
                                clats.append(0)
                                clons.append(0)
                        ret.position.clats = clats
                        ret.position.clons = clons 
                        ret.success = ErrorCode.SUCCESS 
                        ret.info = ErrorCode.ERROR_MESSAGE[ret.success]
                        logging.info("[GE] get clats=%s, clons=%s through lats=%s, lons=%s", 
                                        clats, clons, data.lats, data.lons)
                    else:
                        logging.exception("[GE] get latlon_offset failed.  content: %s", content)
                else:
                    logging.exception("[GE] get latlon_offset failed.  response: %s", response)
                
                # part old: offset single-point
                #response = self.send(ConfHelper.LBMP_CONF.ge_host,
                #                     ConfHelper.LBMP_CONF.ge_url % (data.lat/3600000.0, data.lon/3600000.0),
                #                     None, 
                #                     HTTP.METHOD.GET)
                ## NOTE: the response may be 
                ## {"error":0,"x":"MTEzLjM5Njg3ODY3ODcx","y":"MjIuNTE0NjQ1MDk0NzE="}  or {'error':2,'x':'MA==','y':'MA=='} 
                ## so here change ' to "
                #response = response.replace("'",'"')
                #logging.info('[GE] response:\n %s', response)
                #if response:
                #    json_data = json_decode(response)
                #    if json_data['error'] == 0:
                #        lon = base64.b64decode(json_data['x'])
                #        lat = base64.b64decode(json_data['y'])
                #        ret.position.clat = int(float(lat) * 3600000)
                #        ret.position.clon = int(float(lon) * 3600000)
                #        logging.info("[GE] get clat=%s, clon=%s through lat=%s, lon=%s", 
                #                        lat, lon, data.lat, data.lon)
                #        ret.success = ErrorCode.SUCCESS 
                #        ret.info = ErrorCode.ERROR_MESSAGE[ret.success]
                #    else:
                #        logging.error("[GE] get latlon_offset failed. response:\n %s", response)
                #else:
                #    logging.error("[GE] get latlon_offset failed. response:\n %s", response)

            except Exception as e:
                logging.exception("[GE] get latlon_offset failed. Exception: %s", e.args)

            self.write(ret)
            IOLoop.instance().add_callback(self.finish)

        self.queue.put((LBMP.PRIORITY.GE, _on_finish))
