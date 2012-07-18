#! /usr/bin/enb/python
# -*- coding:utf-8 -*-

import logging 
import os.path
import site

TOP_DIR_ = os.path.abspath(os.path.join(__file__, "../../../.."))
site.addsitedir(os.path.join(TOP_DIR_, "libs"))

TOP_DIR_ = os.path.abspath(os.path.join(__file__, "../../handlers"))
site.addsitedir(TOP_DIR_)

import time, datetime
from calendar import monthrange

import pymongo

from db_.mysql import DBConnection
from db_.mongodb import MongoDBConnection
from constants import XXT
from utils.dotdict import DotDict
from myutils import city_info, start_end_of_month
from helpers.confhelper import ConfHelper

class MSubscriberMixin(object):
       
    def __init__(self):
        self.mysql_db = DBConnection().db

    def retrieve_mixin(self, citylist=None, start_time=None, end_time=None):
  
        results = []
        d = datetime.date.fromtimestamp(start_time/1000)
        year = d.year
        month = d.month
        cities = city_info(citylist, self.mysql_db)
        #optype_status = (XXT.OPER_TYPE.CREATE, XXT.OPER_TYPE.RESUME, XXT.OPER_TYPE.UPDATE)
        for city in cities:
            #new_groups = self.mysql_db.get("SELECT count(*) as total"
            #                               " FROM T_XXT_GROUP"
            #                               " WHERE timestamp BETWEEN %s AND %s"
            #                               " AND city_id = %s",
            #                               start_time, end_time, city.id)
            new_groups = self.mysql_db.get("call P_SUBSCRIBER_NEW_GROUPS(%s, %s, %s)",
                                           start_time, end_time, city.id)  
            #new_parents = self.mysql_db.get("SELECT count(T_XXT_USER.xxt_uid) as total"
            #                                " FROM T_XXT_USER, T_XXT_GROUP"
            #                                " WHERE T_XXT_USER.timestamp BETWEEN %s AND %s"
            #                                " AND optype IN %s"
            #                                " AND group_id = T_XXT_GROUP.xxt_id"
            #                                " AND T_XXT_GROUP.city_id = %s", 
            #                                start_time, end_time, tuple(optype_status), city.id)
            #NOTE: change utc to the format as 201201312359590000
            #only do this way when dealing with timestamp of T_XXT_USER and T_XXT_SUBSCRIPTION_LOG
            start_time_parent =  time.strftime("%Y%m%d%H%M%S0000", time.localtime(start_time/1000))
            end_time_parent =  time.strftime("%Y%m%d%H%M%S9999", time.localtime(start_time/1000))
            new_parents = self.mysql_db.get("call P_SUBSCRIBER_NEW_PARENTS(%s, %s, %s)",
                                            start_time_parent, end_time_parent, city.id)
 
            #new_children = self.mysql_db.get("SELECT count(T_XXT_TARGET.xxt_tid) as total"
            #                                 " FROM T_XXT_TARGET, T_XXT_GROUP"
            #                                 " WHERE T_XXT_TARGET.timestamp BETWEEN %s AND %s"
            #                                 " AND optype IN %s"
            #                                 " AND group_id = T_XXT_GROUP.xxt_id"
            #                                 " AND T_XXT_GROUP.city_id = %s", 
            #                                 start_time, end_time, tuple(optype_status), city.id)
            new_children = self.mysql_db.get("call P_SUBSCRIBER_NEW_CHILDREN(%s, %s, %s)",
                                             start_time, end_time, city.id) 

            #total_groups = self.mysql_db.get("SELECT count(*) as total"
            #                                 " FROM T_XXT_GROUP"
            #                                 " WHERE timestamp <= %s"
            #                                 " AND city_id = %s", 
            #                                 end_time, city.id)
            total_groups = self.mysql_db.get("call P_SUBSCRIBER_TOTAL_GROUPS(%s, %s)",
                                             end_time, city.id) 
            #total_parents = self.mysql_db.get("SELECT count(T_XXT_USER.xxt_uid) as total"
            #                                  " FROM T_XXT_USER, T_XXT_GROUP"
            #                                  " WHERE T_XXT_USER.timestamp <= %s"
            #                                  " AND optype IN %s"
            #                                  " AND group_id = T_XXT_GROUP.xxt_id"
            #                                  " AND T_XXT_GROUP.city_id = %s", 
            #                                  end_time, tuple(optype_status), city.id)
            total_parents = self.mysql_db.get("call P_SUBSCRIBER_TOTAL_PARENTS(%s, %s)",
                                              end_time_parent, city.id) 
            #total_children = self.mysql_db.get("SELECT count(T_XXT_TARGET.xxt_tid) as total"
            #                                   " FROM T_XXT_TARGET, T_XXT_GROUP"
            #                                   " WHERE T_XXT_TARGET.timestamp <= %s"
            #                                   " AND optype IN %s"
            #                                   " AND group_id = T_XXT_GROUP.xxt_id"
            #                                   " AND T_XXT_GROUP.city_id = %s", 
            #                                   end_time, tuple(optype_status), city.id)
            total_children = self.mysql_db.get("call P_SUBSCRIBER_TOTAL_CHILDREN(%s, %s)",
                                               end_time, city.id) 
            res = {'_id': None,
                   'province_id':city.p_id,
                   'city_id': city.id,
                   'province':city.p_name,
                   'city':city.name,
                   'new_groups': new_groups.total,
                   'new_parents': new_parents.total,
                   'new_children': new_children.total,
                   'total_groups': total_groups.total,
                   'total_parents': total_parents.total,
                   'total_children': total_children.total,
                   'year': year,
                   'month': month}
            results.append(res)
        return results

class MSubscriber(MSubscriberMixin):
    """This class mainly retrieves data from MySQL as intermediate result
       and stores them into MongoDB.
    """
    def __init__(self):
        MSubscriberMixin.__init__(self)
        try:
            self.mongodb_db = MongoDBConnection().db
            self.collection = self.mongodb_db.subscriber
            self.collection.ensure_index([('city_id', pymongo.ASCENDING),
                                          ('year', pymongo.DESCENDING),
                                          ('month', pymongo.DESCENDING)])
        except:
            logging.exception('mongodb connected failed')

    def retrieve(self, citylist=None, start_time=None, end_time=None):
        """core for Retrieving and Storing operation."""
        #store the complete data of current month or last month into MongoDB
        if not(start_time and end_time):
            start_time, end_time = start_end_of_month()

        if not citylist:
            cities = self.mysql_db.query("SELECT DISTINCT region_code AS id FROM T_HLR_CITY")
            citylist = [c.id for c in cities]

        results = self.retrieve_mixin(citylist, start_time, end_time)
        try:
            for result in results:
                result = DotDict(result)
                oldresult = self.collection.find_one({'city_id': result.city_id, 'year': result.year, 'month': result.month})
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
    ins = MSubscriber()
    ins.retrieve()

if __name__ == "__main__":
    main()
