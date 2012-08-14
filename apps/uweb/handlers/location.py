# -*- coding: utf-8 -*-

import logging

from tornado.escape import json_decode, json_encode
import tornado.web

from helpers.lbmpsenderhelper import LbmpSenderHelper
from helpers.queryhelper import QueryHelper
from utils.dotdict import DotDict
from utils.misc import safe_utf8, get_location_cache_key
from constants import LOCATION

from base import BaseHandler, authenticated


class LocationHandler(BaseHandler):
    """Get location description for the point."""

    def update_location_name(self, name, id):
        self.db.execute("UPDATE T_LOCATION"
                        "  SET name = %s"
                        "  WHERE id = %s",
                        safe_utf8(name), id)


    @authenticated
    @tornado.web.removeslash
    @tornado.web.asynchronous
    def post(self):
        """
        @params: location.longitude and location.latitude
        when we get longitude and latitude via GPS or CELLID, but can not
        get clongitude and clatitude from GE(clongtitude=clatitude=0), we'd
        better get it firstly, then to get name from GV
        """
        try:
            location = DotDict(json_decode(self.request.body))
        except:
            self.write_ret(ErrorCode.ILLEGAL_DATA_FORMAT)
            self.finish()
            return

        key = get_location_cache_key(location.longitude, location.latitude)
        location.name = self.redis.getvalue(key)
       
        def _on_finish(response):
            try:
                response = json_decode(response)
                if response['success'] == 0:
                    location.name = response.get('location').get('name')
                    if location.name:
                        self.redis.setvalue(key, location.name, LOCATION.MEMCACHE_EXPIRY)
                        if location.id:
                            self.update_location_name(location.name, location.id) 
                    else:
                        location.name = None
                else:
                    location.name = None
                    logging.info("Get location name error: %s, sim: %s",
                                 response.get('info'), self.current_user.sim)
            except Exception as e:
                logging.warn("Get location name error: %s, Sim: %s",
                             e.args, self.current_user.sim)
            _on_finish2(location)


        def _on_finish2(location):
            self.set_header(*self.JSON_HEADER)
            self.write(json_encode(location))
            self.finish()

        if not location.name:
            flag = True
            if location.clongitude == 0 or location.clatitude == 0:
                # never do it
                # get clongitude and clatitude from GE
                try:
                    response = LbmpSenderHelper.forward(LbmpSenderHelper.URLS.GE, location)
                    response = json_decode(response)
                    if response['success'] == 0:
                        location.clatitude = response['position']['clat']
                        location.clongitude = response['position']['clon']
                    else:
                        logging.info("Get clocation from GE error: %s, sim: %s",
                                     response['info'], self.current_user.sim)
                        flag = False
                except Exception as e:
                    logging.warn("Get clocation from GE error: %s, sim: %s",
                                 e.args, self.current_user.sim)
                    flag = False
                
            if flag:
               # get location name from GV
                try:
                    group = QueryHelper.get_group_from_sim(self.current_user.sim, self.db)
                    args = dict(lon=(float(location.clongitude)/3600000),
                                lat=(float(location.clatitude)/3600000),
                                group=group)
                    LbmpSenderHelper.async_forward(LbmpSenderHelper.URLS.GV, args, _on_finish)
                except Exception as e:
                    logging.warn("Get location name error: %s, sim: %s",
                                 e.args, self.current_user.sim)
        else: 
            _on_finish2(location)

