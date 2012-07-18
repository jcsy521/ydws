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

import pymongo

from db_.mysql import DBConnection
from db_.mongodb import MongoDBConnection
from constants import LOCATION, XXT, PRIVILEGES, SMS
from myutils import city_info, start_end_of_month
from utils.dotdict import DotDict
from helpers.confhelper import ConfHelper
from utils.misc import DUMMY_IDS


class MMonthlyMixin(object):
 
    def __init__(self):
        self.mysql_db = DBConnection().db

    def retrieve_mixin(self, city_list=None, start_time=None, end_time=None):
        results = []
        d = datetime.date.fromtimestamp(start_time/1000)
        year = d.year
        month = d.month
        cities = city_info(city_list, self.mysql_db)
        for city in cities:
            #sql = "SELECT count(*) AS new_groups" + \
            #      " FROM T_XXT_GROUP" + \
            #      " WHERE timestamp BETWEEN %s AND %s" + \
            #      " AND city_id = %s"

            #sql = sql % (start_time, end_time, city.id)
            #new_groups = self.mysql_db.get(sql)
            new_groups = self.mysql_db.get("call P_MONTHLY_NEW_GROUPS(%s, %s, %s)",
                                           start_time, end_time, city.id) 
            
            #sql = "SELECT count(T_XXT_USER.xxt_uid) as total" + \
            #      " FROM T_XXT_USER, T_XXT_GROUP" + \
            #      " WHERE T_XXT_USER.timestamp BETWEEN %s AND %s" + \
            #      " AND optype IN (1,3,4)" + \
            #      " AND group_id = T_XXT_GROUP.xxt_id" + \
            #      " AND T_XXT_GROUP.city_id = %s"

            #sql = sql % (start_time, end_time, XXT.VALID.VALID, city.id)
            #new_parents = self.mysql_db.get(sql)
            #NOTE: change utc to the format as 201201312359590000
            #only do this way when dealing with time of  T_XXT_USER and T_XXT_SUBSCRIPTION_LOG
            start_time_parent =  time.strftime("%Y%m%d%H%M%S0000", time.localtime(start_time/1000))
            end_time_parent =  time.strftime("%Y%m%d%H%M%S9999", time.localtime(start_time/1000))
            new_parents = self.mysql_db.get("call P_MONTHLY_NEW_PARENTS(%s, %s, %s)",
                                            start_time_parent, end_time_parent, city.id) 
            #sql = "SELECT count(T_XXT_TARGET.xxt_tid) as total" + \
            #      " FROM T_XXT_TARGET, T_XXT_GROUP" + \
            #      " WHERE T_XXT_TARGET.timestamp BETWEEN %s AND %s" + \
            #      " AND valid = %s" + \
            #      " AND group_id = T_XXT_GROUP.xxt_id" + \
            #      " AND T_XXT_GROUP.city_id = %s"
            #sql = sql % (start_time, end_time, XXT.VALID.VALID, city.id)
            #new_children = self.mysql_db.get(sql)
            new_children = self.mysql_db.get("call P_MONTHLY_NEW_CHILDREN(%s, %s, %s)",
                                             start_time, end_time, city.id) 

            #sql = "SELECT count(*) as total" + \
            #      " FROM T_XXT_GROUP" + \
            #      " WHERE timestamp <= %s" + \
            #      " AND city_id = %s" 
            #sql = sql % (end_time, city.id)
            #total_groups = self.mysql_db.get(sql)
            total_groups = self.mysql_db.get("call P_MONTHLY_TOTAL_GROUPS(%s, %s)", 
                                             end_time, city.id)

            #sql = "SELECT count(T_XXT_USER.xxt_uid) as total" + \
            #      " FROM T_XXT_USER, T_XXT_GROUP" + \
            #      " WHERE T_XXT_USER.timestamp <= %s" + \
            #      " AND optype IN (1, 3, 4)" + \
            #      " AND group_id = T_XXT_GROUP.xxt_id" + \
            #      " AND T_XXT_GROUP.city_id = %s" 
            #sql = sql % (end_time, XXT.VALID.VALID, city.id)
            #total_parents = self.mysql_db.get(sql)
            total_parents = self.mysql_db.get("call P_MONTHLY_TOTAL_PARENTS(%s, %s)",
                                              end_time_parent, city.id) 

            #sql = "SELECT count(T_XXT_TARGET.xxt_tid) as total" + \
            #      " FROM T_XXT_TARGET, T_XXT_GROUP" + \
            #      " WHERE T_XXT_TARGET.timestamp <= %s" + \
            #      " AND optyped IN (1, 3, 4)" + \
            #      " AND group_id = T_XXT_GROUP.xxt_id" + \
            #      " AND T_XXT_GROUP.city_id = %s" 
            #sql = sql % (end_time, XXT.VALID.VALID, city.id)
            #total_children = self.mysql_db.get(sql)
            total_children = self.mysql_db.get("call P_MONTHLY_TOTAL_CHILDREN(%s, %s)", 
                                               end_time, city.id)

            #sql = "SELECT count(T_SMS_LOG.id) as total" + \
            #      " FROM T_SMS_LOG" + \
            #      " WHERE T_SMS_LOG.category = %s" + \
            #      " AND T_SMS_LOG.fetchtime BETWEEN %s AND %s" + \
            #      " AND ((T_SMS_LOG.mobile in" + \
            #      " (SELECT mobile FROM T_XXT_USER, T_XXT_GROUP" + \
            #      " WHERE T_XXT_USER.group_id = T_XXT_GROUP.xxt_id" + \
            #      " AND T_XXT_GROUP.city_id = %s)) OR " + \
            #      " (T_SMS_LOG.mobile in" + \
            #      " (SELECT mobile FROM T_XXT_TARGET, T_XXT_GROUP" + \
            #      " WHERE T_XXT_TARGET.group_id = T_XXT_GROUP.xxt_id" + \
            #      " AND T_XXT_GROUP.city_id = %s)))"
            #sql = sql % (SMS.CATEGORY.RECEIVE, start_time, end_time, city.id, city.id)
            #mo_sms = self.mysql_db.get(sql)
            
            mobile_parents = self.mysql_db.query("SELECT mobile" 
                                                 "  FROM T_XXT_USER, T_XXT_GROUP"
                                                 "  WHERE T_XXT_USER.group_id = T_XXT_GROUP.xxt_id"
                                                 "  AND T_XXT_GROUP.city_id = %s",
                                                 city.id)
            mobile_children = self.mysql_db.query("SELECT mobile" 
                                                 "  FROM T_XXT_TARGET, T_XXT_GROUP"
                                                 "  WHERE T_XXT_TARGET.group_id = T_XXT_GROUP.xxt_id"
                                                 "  AND T_XXT_GROUP.city_id = %s",
                                                 city.id)
            mobiles=[]
            mobiles.extend(mobile_parents)
            mobiles.extend(mobile_children)
            mobiles = [int(mobile['mobile']) for mobile in mobiles]
            mo_sms = self.mysql_db.get("SELECT count(T_SMS_LOG.id) as total"
                                       "  FROM T_SMS_LOG"
                                       "  WHERE T_SMS_LOG.category = %s"
                                       "  AND fetchtime BETWEEN %s AND %s"
                                       "  AND T_SMS_LOG.mobile IN %s",
                                       SMS.CATEGORY.RECEIVE, start_time, end_time,
                                       tuple(mobiles + DUMMY_IDS))

            #mo_sms = self.mysql_db.get("call P_MONTHLY_MO_SMS(%s, %s, %s, %s)",
            #                           SMS.CATEGORY.RECEIVE, start_time, end_time, city.id)

            #sql = "SELECT count(T_SMS_LOG.id) as total" + \
            #      " FROM T_SMS_LOG" + \
            #      " WHERE T_SMS_LOG.category = %s"  + \
            #      " AND T_SMS_LOG.fetchtime BETWEEN %s AND %s" + \
            #      " AND ((T_SMS_LOG.mobile in" + \
            #      " (SELECT mobile FROM T_XXT_USER, T_XXT_GROUP" + \
            #      " WHERE T_XXT_USER.group_id = T_XXT_GROUP.xxt_id" + \
            #      " AND T_XXT_GROUP.city_id = %s)) OR " + \
            #      " (T_SMS_LOG.mobile in" + \
            #      " (SELECT mobile FROM T_XXT_TARGET, T_XXT_GROUP" + \
            #      " WHERE T_XXT_TARGET.group_id = T_XXT_GROUP.xxt_id" + \
            #      " AND T_XXT_GROUP.city_id = %s)))"
            #sql = sql % (SMS.CATEGORY.SEND, start_time, end_time, city.id, city.id)
            #mt_sms = self.mysql_db.get(sql)
            # mt_sms and mo_sms use the same procedure#
            #mt_sms = self.mysql_db.get("call P_MONTHLY_MO_SMS(%s, %s, %s, %s)",
            #                           SMS.CATEGORY.SEND, start_time, end_time, city.id) 
            mt_sms = self.mysql_db.get("SELECT count(T_SMS_LOG.id) as total"
                                       "  FROM T_SMS_LOG"
                                       "  WHERE T_SMS_LOG.category = %s"
                                       "  AND fetchtime BETWEEN %s AND %s"
                                       "  AND T_SMS_LOG.mobile IN %s",
                                       SMS.CATEGORY.SEND, start_time, end_time,
                                       tuple(mobiles + DUMMY_IDS))
            
            # In fact, total_sms = mo_sms + mt_sms
            # there is of no necessity to query the database
            #sql = "SELECT count(T_SMS_LOG.id) as total" + \
            #      " FROM T_SMS_LOG" + \
            #      " WHERE T_SMS_LOG.fetchtime BETWEEN %s AND %s" + \
            #      " AND ((T_SMS_LOG.mobile in" + \
            #      " (SELECT mobile FROM T_XXT_USER, T_XXT_GROUP" + \
            #      " WHERE T_XXT_USER.group_id = T_XXT_GROUP.xxt_id" + \
            #      " AND T_XXT_GROUP.city_id = %s)) OR " + \
            #      " (T_SMS_LOG.mobile in" + \
            #      " (SELECT mobile FROM T_XXT_TARGET, T_XXT_GROUP" + \
            #      " WHERE T_XXT_TARGET.group_id = T_XXT_GROUP.xxt_id" + \
            #      " AND T_XXT_GROUP.city_id = %s)))"
            #sql = sql % (start_time, end_time, city.id, city.id)
            #total_sms = self.mysql_db.get(sql)

            #sql = "SELECT count(*) as total" + \
            #      " FROM T_LOCATION, T_LBMP_TERMINAL, T_XXT_TARGET, T_XXT_GROUP" + \
            #      " WHERE category = %s" + \
            #      " AND T_LOCATION.timestamp BETWEEN %s AND %s" + \
            #      " AND T_LOCATION.sim = T_LBMP_TERMINAL.sim" + \
            #      " AND T_LBMP_TERMINAL.sim = T_XXT_TARGET.mobile" + \
            #      " AND T_XXT_TARGET.group_id = T_XXT_GROUP.xxt_id" + \
            #      " AND T_XXT_GROUP.city_id = %s"
            #sql = sql % (LOCATION.CATEGORY.CUSTOM, start_time, end_time, city.id)
            #custom = self.mysql_db.get(sql)
            #custom = self.mysql_db.get("call P_MONTHLY_CUSTOM(%s, %s, %s, %s)",
            #                           LOCATION.CATEGORY.CUSTOM, start_time, end_time, city.id)

            # custom, schedule and realtime use the same schedule 
            #sql = "SELECT count(*) as total" + \
            #      " FROM T_LOCATION, T_LBMP_TERMINAL, T_XXT_TARGET, T_XXT_GROUP" + \
            #      " WHERE category = %s" + \
            #      " AND T_LOCATION.timestamp BETWEEN %s AND %s" + \
            #      " AND T_LOCATION.sim = T_LBMP_TERMINAL.sim" + \
            #      " AND T_LBMP_TERMINAL.sim = T_XXT_TARGET.mobile" + \
            #      " AND T_XXT_TARGET.group_id = T_XXT_GROUP.xxt_id" + \
            #      " AND T_XXT_GROUP.city_id = %s"
            #sql = sql % (LOCATION.CATEGORY.SCHEDULE, start_time, end_time, city.id)
            #schedule = self.mysql_db.get(sql)
            schedule = self.mysql_db.get("call P_MONTHLY_CUSTOM(%s, %s, %s, %s)",
                                         LOCATION.CATEGORY.SCHEDULE, start_time, end_time, city.id)
 

            #sql = "SELECT count(*) as total" + \
            #      " FROM T_LOCATION, T_LBMP_TERMINAL, T_XXT_TARGET, T_XXT_GROUP" + \
            #      " WHERE category = %s" + \
            #      " AND T_LOCATION.timestamp BETWEEN %s AND %s" + \
            #      " AND T_LOCATION.sim = T_LBMP_TERMINAL.sim" + \
            #      " AND T_LBMP_TERMINAL.sim = T_XXT_TARGET.mobile" + \
            #      " AND T_XXT_TARGET.group_id = T_XXT_GROUP.xxt_id" + \
            #      " AND T_XXT_GROUP.city_id = %s"
            #sql = sql % (LOCATION.CATEGORY.REALTIME, start_time, end_time, city.id)
            #realtime = self.mysql_db.get(sql)
            realtime = self.mysql_db.get("call P_MONTHLY_CUSTOM(%s, %s, %s, %s)",
                                         LOCATION.CATEGORY.REALTIME, start_time, end_time, city.id)

            #sql = "SELECT count(*) as total" + \
            #      " FROM T_LOCATION, T_LBMP_TERMINAL, T_XXT_TARGET, T_XXT_GROUP" + \
            #      " WHERE (category = %s OR category = %s)" + \
            #      " AND T_LOCATION.timestamp BETWEEN %s AND %s" + \
            #      " AND T_LOCATION.sim = T_LBMP_TERMINAL.sim" + \
            #      " AND T_LBMP_TERMINAL.sim = T_XXT_TARGET.mobile" + \
            #      " AND T_XXT_TARGET.group_id = T_XXT_GROUP.xxt_id" + \
            #      " AND T_XXT_GROUP.city_id = %s"
            #sql = sql % (LOCATION.CATEGORY.REGION_ENTER,
            #             LOCATION.CATEGORY.REGION_OUT, start_time, end_time, city.id)
            #bound = self.mysql_db.get(sql)
            bound = self.mysql_db.get("call P_MONTHLY_BOUND(%s, %s, %s, %s, %s)",
                                      LOCATION.CATEGORY.REGION_ENTER, LOCATION.CATEGORY.REGION_OUT, start_time, end_time, city.id)

            #sql = "SELECT count(*) as total" + \
            #      " FROM T_LOCATION, T_LBMP_TERMINAL, T_XXT_TARGET, T_XXT_GROUP" + \
            #      " WHERE category = %s" + \
            #      " AND T_LOCATION.timestamp BETWEEN %s AND %s" + \
            #      " AND T_LOCATION.sim = T_LBMP_TERMINAL.sim" + \
            #      " AND T_LBMP_TERMINAL.sim = T_XXT_TARGET.mobile" + \
            #      " AND T_XXT_TARGET.group_id = T_XXT_GROUP.xxt_id" + \
            #      " AND T_XXT_GROUP.city_id = %s"
            #sql = sql % (LOCATION.CATEGORY.POWERLOW, start_time, end_time, city.id)
            #power = self.mysql_db.get(sql)
            power = self.mysql_db.get("call P_MONTHLY_POWER(%s, %s, %s, %s)",
                                      LOCATION.CATEGORY.POWERLOW, start_time, end_time, city.id)

            #sql = "SELECT count(*) as total" + \
            #      " FROM T_LOCATION, T_LBMP_TERMINAL, T_XXT_TARGET, T_XXT_GROUP" + \
            #      " WHERE category = %s" + \
            #      " AND T_LOCATION.timestamp BETWEEN %s AND %s" + \
            #      " AND T_LOCATION.sim = T_LBMP_TERMINAL.sim" + \
            #      " AND T_LBMP_TERMINAL.sim = T_XXT_TARGET.mobile" + \
            #      " AND T_XXT_TARGET.group_id = T_XXT_GROUP.xxt_id" + \
            #      " AND T_XXT_GROUP.city_id = %s"
            #sql = sql % (LOCATION.CATEGORY.EMERGENCY, start_time, end_time, city.id)
            #sos = self.mysql_db.get(sql)
            sos = self.mysql_db.get("call P_MONTHLY_SOS(%s, %s, %s, %s)",
                                    LOCATION.CATEGORY.EMERGENCY, start_time, end_time, city.id)
 
            res = {'_id': None,
                   'province_id': city.p_id,
                   'city_id': city.id,
                   'province': city.p_name,
                   'city': city.name,
                   'new_groups': new_groups.total,
                   'new_parents': new_parents.total,
                   'new_children': new_children.total,
                   'total_groups': total_groups.total,
                   'total_parents': total_parents.total,
                   'total_children': total_children.total,
                   'total_sms': mt_sms.total + mo_sms.total,
                   'mt_sms': mt_sms.total,
                   'mo_sms': mo_sms.total,
                   #'custom': custom.total,
                   'schedule': schedule.total,
                   'realtime': realtime.total,
                   'bound': bound.total,
                   'sos': sos.total,
                   'power': power.total,
                   'year': year,
                   'month': month}

            results.append(res)
        return results


class MMonthly(MMonthlyMixin):
    """This class mainly retrieves data from MySQL as intermediate result
       and stores them into MongoDB.
    """
    def __init__(self):
        MMonthlyMixin.__init__(self)
        try:
            self.mongodb_db = MongoDBConnection().db 
            self.collection = self.mongodb_db.monthly
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

        results =  self.retrieve_mixin(city_list, start_time, end_time)
        try:
            for result in results:
                result = DotDict(result)
                query_term = {'city_id': result.city_id, 'year': result.year, 'month':result.month}
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
    ins = MMonthly()
    ins.retrieve()

if __name__ == "__main__":
    main()
