# -*- coding: utf-8 -*-


"""
A instance:
url: 
http://api.map.baidu.com/geoconv/v1/?coords=114,29;113,28&from=1&to=5&ak=DD8efee89860f59163512b729edbb4b1
response:
{"status":0,"result":[{"x":114.0118726607,"y":29.003357119043},{"x":113.01217365665,"y":28.002600910186}]}

For more infomation: 
http://developer.baidu.com/map/changeposition.htm
"""

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
        @params: lons:[lon,// degree * 3600000 
                       lon, 
                       ...},
                 lats:[lat, //degree * 3600000
                       lat,
                       ...]
        @returns: ret = {success=status,
                         info=message,
                         position={clons:[clon,//degree * 3600000,
                                          clon,
                                          ...],
                                   clats=[clat,//degree * 3600000,
                                          clat,
                                          ...]}
                        }
        """
        ret=DotDict(success=ErrorCode.LOCATION_OFFSET_FAILED,
                    info=ErrorCode.ERROR_MESSAGE[ErrorCode.LOCATION_OFFSET_FAILED],
                    position=DotDict(clats=[],
                                     clons=[]))
        try:
            data = DotDict(json_decode(self.request.body))
            logging.info("[GE] request:\n %s", data)
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

                clats = []
                clons = []
                
                coords_lst = [] 
                coords = ''
                for lat, lon in latlons:
                    coord=','.join([str(lon/3600000.0), str(lat/3600000.0)])
                    coords_lst.append(coord)
                coords = ';'.join(coords_lst)
                    
                response, content = self.http.request(ConfHelper.LBMP_CONF.ge_multipoints_url_geoconv % (coords), HTTP.METHOD.GET)

                logging.info("[GE] response:\n %s, \ncontent:\n %s", response, content)
                if response['status'] == '200':
                    if content:
                        #{"status":0,
                        #"result":[{"x":114.01186831848,"y":29.003351445294},
                        #{"x":113.01216690363,"y":28.002601877919}]}
                        ret.success = ErrorCode.SUCCESS 
                        ret.info = ErrorCode.ERROR_MESSAGE[ret.success]
                        json_datas = json_decode(content)
                        if json_datas['status'] == 0: # 
                            clatlon = json_datas['result']
                            for i, result in enumerate(clatlon):
                                clons.append(int(float(result['x'])*3600000))
                                clats.append(int(float(result['y'])*3600000))
                                ret.position.clats = clats
                                ret.position.clons = clons 
                                ret.success = ErrorCode.SUCCESS 
                                ret.info = ErrorCode.ERROR_MESSAGE[ret.success]
                                logging.info("[GE] Get clats=%s, clons=%s through lats=%s, lons=%s", 
                                                clats, clons, data.lats, data.lons)
                        else:
                            logging.exception("[GE] Get latlon_offset failed. content: %s", content)

                    else:
                        logging.exception("[GE] Get latlon_offset failed. content: %s", content)
                else:
                    logging.exception("[GE] Get latlon_offset failed. response: %s", response)
                
            except Exception as e:
                logging.exception("[GE] Get latlon_offset failed. Exception: %s", e.args)

            self.write(ret)
            IOLoop.instance().add_callback(self.finish)

        self.queue.put((LBMP.PRIORITY.GE, _on_finish))
