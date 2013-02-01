#! /usr/bin/enb/python
# -*- coding:utf-8 -*-

import logging 
import os.path
import site

TOP_DIR_ = os.path.abspath(os.path.join(__file__, "../../../.."))
site.addsitedir(os.path.join(TOP_DIR_, "libs"))

TOP_DIR_ = os.path.abspath(os.path.join(__file__, "../../handlers"))
site.addsitedir(TOP_DIR_)

from calendar import monthrange
import time, datetime

import tornado

from db_.mysql import DBConnection
from constants import LOCATION
from utils.dotdict import DotDict
from myutils import city_info, start_end_of_month

from helpers.confhelper import ConfHelper


class MLocationMixin(object):
   
    def __init__(self):
        self.mysql_db = DBConnection().db
 
    def retrieve_mixin(self, city_list=None, start_time=None, end_time=None):
       
        results = []
        d = datetime.date.fromtimestamp(start_time/1000)
        year = d.year
        month = d.month
        cities = city_info(city_list, self.mysql_db)
        for city in cities:
            groups = self.mysql_db.query("SELECT T_XXT_GROUP.name as group_name, T_XXT_GROUP.xxt_id"
                                         " FROM T_XXT_GROUP WHERE T_XXT_GROUP.city_id = %s",
                                         city.id)
            for group in groups: 
                for item, category in [ #('custom', LOCATION.CATEGORY.CUSTOM),
                                       ('schedule', LOCATION.CATEGORY.SCHEDULE),
                                       ('realtime', LOCATION.CATEGORY.REALTIME)]:
                    #data = self.mysql_db.get("SELECT count(T_LOCATION.id) as total"
                    #                         " FROM T_LOCATION, T_XXT_TARGET, T_LBMP_TERMINAL"
                    #                         " WHERE T_LOCATION.timestamp BETWEEN %s AND %s" 
                    #                         " AND T_LOCATION.category = %s"
                    #                         " AND T_LOCATION.sim = T_LBMP_TERMINAL.sim"
                    #                         " AND T_LBMP_TERMINAL.sim = T_XXT_TARGET.mobile"
                    #                         " AND T_XXT_TARGET.group_id = %s",
                    #                         start_time, end_time, category, group.xxt_id)
                    data = self.mysql_db.get("call P_LOCATION(%s, %s, %s, %s)",
                                             start_time, end_time, category, group.xxt_id) 
                    group[item] = data.total

                res = {'_id': None,
                       'province_id': city.p_id,
                       'city_id': city.id,
                       'group_id': group.xxt_id,
                       'province': city.p_name,
                       'city': city.name,
                       'group_name': group.group_name,
                       # 'custom': group.custom,
                       'schedule': group.schedule,
                       'realtime': group.realtime,
                       'year': year,
                       'month': month}
                results.append(res)
        return results


class MLocation(MLocationMixin):
    """This class mainly retrieves data from MySQL as intermediate result
       and stores them into MongoDB.
    """
    def __init__(self):
        MLocationMixin.__init__(self)
        try:
            self.collection = self.mongodb_db.location
            self.collection.ensure_index([('city_id', pymongo.ASCENDING),
                                          ('year', pymongo.DESCENDING),
                                          ('month', pymongo.DESCENDING)])
        except:
            logging.exception('mongodb connected failed')

    def retrieve(self, city_list=None, start_time=None, end_time=None):
        """core for Retrieving and Storing operation."""
        #store the complete data of current month or last month into MongoDB
        if not (start_time and end_time):
            start_time, end_time = start_end_of_month()

        if not city_list:
            cities = self.mysql_db.query("SELECT DISTINCT region_code AS id FROM T_HLR_CITY")
            city_list = [city.id for city in cities]

        results = self.retrieve_mixin(city_list, start_time, end_time)
        try: 
            for result in results:
                result = DotDict(result)
                query_term = {'group_id': result.group_id, 'year': result.year, 'month': result.month}
                oldresult = self.collection.find_one(query_term)
                if oldresult:
                    result['_id'] = oldresult['_id']
                else:
                    result.pop('_id')
                self.collection.save(result)
        except:
            logging.exception('mongodb connected failed')
        return results

def main():
    ConfHelper.load('../../../conf/global.conf')
    ins = MLocation()
    ins.retrieve()

if __name__ == "__main__":
    main()
