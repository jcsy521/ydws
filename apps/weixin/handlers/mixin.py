# -*- coding:utf-8 -*-

from utils.misc import safe_utf8
from urllib import quote
from time import strftime

from constants import AREA
from utils.misc import DUMMY_IDS
from utils.dotdict import DotDict


class BaseMixin(object):
    """
    This class is responsible for offering basic functions
    or common used functions.
    """
    # memcached expires time, in seconds
    MEMCACHE_EXPIRY = 60 * 5 # 5 minutes

    def get_memcache_key(self, hash_):

        return self.KEY_TEMPLATE % (self.current_user.id, hash_)

    def generate_file_name(self, file_name):

        if "MSIE" in self.request.headers['User-Agent']:
            file_name = quote(safe_utf8(file_name))
        return '-'.join((file_name, strftime("%Y%m%d")))

    def get_area_memcache_key(self, administrator_id):
        
        return "administrator_id:%s" % (administrator_id,)

    def get_area(self, city_ids):
        areas = []
        city_ids = list(set(city_ids))
        areas = self.db.query("SELECT city_id, city_name"
                              "  FROM T_HLR_CITY"
                              "  WHERE city_id IN %s",
                              tuple(city_ids + DUMMY_IDS))

        return areas

    def get_privilege_area(self, administrator_id):
        """
        @param administrator_id

        @return privilege_ares from db
        """
        areas = []
        res = self.db.query("SELECT area_id, category FROM T_AREA_PRIVILEGE"
                            "  WHERE administrator_id = %s", 
                            administrator_id)
        if not res:
            return areas

        cs = []
        for r in res:
            if r.category == AREA.CATEGORY.PROVINCE:
                if r.area_id == AREA.ALL_PROVINCES:
                    provinces = self.db.query("SELECT province_id, province_name"
                                              "  FROM T_HLR_PROVINCE"
                                              "  WHERE country_id = 1")
                else:
                    provinces = self.db.query("SELECT province_id, province_name"
                                              "  FROM T_HLR_PROVINCE"
                                              "  WHERE province_id = %s",
                                              r.area_id)
                for province in provinces:
                    cities = self.db.query("SELECT city_id, city_name"
                                           "  FROM T_HLR_CITY"
                                           "  WHERE province_id = %s",
                                           province.province_id)    
                    areas.extend(cities)
            else:
                cs.append(r)
        if cs:
            cids = [c.area_id for c in cs]
            cids = list(set(cids))
            areas = self.db.query("SELECT city_id, city_name"
                                  "  FROM T_HLR_CITY"
                                  "  WHERE region_code IN %s",
                                  tuple(cids + DUMMY_IDS))

        return areas
