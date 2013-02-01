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
from dateutil.relativedelta import relativedelta

from db_.mysql import DBConnection
from constants import LOCATION, XXT, SMS
from utils.dotdict import DotDict
from myutils import city_info
from utils.misc import DUMMY_IDS

from helpers.confhelper import ConfHelper


class MDailyMixin(object):

    def __init__(self):
        self.mysql_db = DBConnection().db
        self.collection = self.mongodb_db.daily

    def retrieve_mixin(self, city_list=None, end_time=None):
        results = []
        cities = city_info(city_list, self.mysql_db)
        #optype_status = (XXT.OPER_TYPE.CREATE, XXT.OPER_TYPE.RESUME, XXT.OPER_TYPE.UPDATE)
        for city in cities:
            #total_groups = self.mysql_db.get("SELECT count(*) as total"
            #                                 " FROM T_XXT_GROUP"
            #                                 " WHERE timestamp <= %s"
            #                                 " AND city_id = %s",
            #                                 end_time, city.id)
            total_groups = self.mysql_db.get("call P_DAILY_TOTAL_GROUPS(%s, %s)",
                                             end_time, city.id)
            #total_parents = self.mysql_db.get("SELECT count(T_XXT_USER.xxt_uid) as total"
            #                                  " FROM T_XXT_USER, T_XXT_GROUP"
            #                                  " WHERE T_XXT_USER.timestamp <= %s"
            #                                  " AND optype IN %s"
            #                                  " AND group_id = T_XXT_GROUP.xxt_id"
            #                                  " AND T_XXT_GROUP.city_id = %s",
            #                                  end_time, tuple(optype_status), city.id)
            #NOTE: change utc to the format as 201201312359590000
            end_time_parent =  time.strftime("%Y%m%d%H%M%S9999", time.localtime(end_time/1000))
            total_parents = self.mysql_db.get("call P_DAILY_TOTAL_PARENTS(%s, %s, %s)",
                                              end_time_parent, XXT.VALID.VALID, city.id)
            #total_children = self.mysql_db.get("SELECT count(T_XXT_TARGET.xxt_tid) as total"
            #                                   " FROM T_XXT_TARGET, T_XXT_GROUP"
            #                                   " WHERE T_XXT_TARGET.timestamp <= %s"
            #                                   " AND optype IN %s"
            #                                   " AND group_id = T_XXT_GROUP.xxt_id"
            #                                   " AND T_XXT_GROUP.city_id = %s",
            #                                   end_time, tuple(optype_status), city.id)
            total_children = self.mysql_db.get("call P_DAILY_TOTAL_CHILDREN(%s, %s, %s)",
                                               end_time, XXT.VALID.VALID, city.id)
            #mo_sms = self.mysql_db.get("SELECT count(T_SMS_LOG.id) as total"
            #                           " FROM T_SMS_LOG"
            #                           " WHERE T_SMS_LOG.category = %s"
            #                           " AND T_SMS_LOG.fetchtime <= %s"
            #                           " AND ((T_SMS_LOG.mobile in"
            #                           " (SELECT mobile FROM T_XXT_USER, T_XXT_GROUP"
            #                           " WHERE T_XXT_USER.group_id = T_XXT_GROUP.xxt_id"
            #                           " AND T_XXT_GROUP.city_id = %s)) OR "
            #                           " (T_SMS_LOG.mobile in"
            #                           " (SELECT mobile FROM T_XXT_TARGET, T_XXT_GROUP"
            #                           " WHERE T_XXT_TARGET.group_id = T_XXT_GROUP.xxt_id"
            #                           " AND T_XXT_GROUP.city_id = %s)))",
            #                           SMS.CATEGORY.RECEIVE,
            #                           end_time, city.id, city.id)
            #mo_sms = self.mysql_db.get("call P_DAILY_MO_SMS(%s, %s, %s)",
            #                           SMS.CATEGORY.RECEIVE, end_time, city.id) 
            #NOTE: get mobiles for parents and children, then query sms_log through it
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
                                       "  AND fetchtime <= %s"
                                       "  AND T_SMS_LOG.mobile IN %s",
                                       SMS.CATEGORY.RECEIVE, end_time,
                                       tuple(mobiles + DUMMY_IDS))
            #mt_sms = self.mysql_db.get("SELECT count(T_SMS_LOG.id) as total"
            #                           " FROM T_SMS_LOG"
            #                           " WHERE T_SMS_LOG.category = %s"
            #                           " AND T_SMS_LOG.fetchtime <= %s"
            #                           " AND ((T_SMS_LOG.mobile in"
            #                           " (SELECT mobile FROM T_XXT_USER, T_XXT_GROUP"
            #                           " WHERE T_XXT_USER.group_id = T_XXT_GROUP.xxt_id"
            #                           " AND T_XXT_GROUP.city_id = %s)) OR "
            #                           " (T_SMS_LOG.mobile in"
            #                           " (SELECT mobile FROM T_XXT_TARGET, T_XXT_GROUP"
            #                           " WHERE T_XXT_TARGET.group_id = T_XXT_GROUP.xxt_id"
            #                           " AND T_XXT_GROUP.city_id = %s)))",
            #                           SMS.CATEGORY.SEND,
            #                           end_time, city.id, city.id)
            # mt_sms and mo_sms call the same procedure
            #mt_sms = self.mysql_db.get("call P_DAILY_MO_SMS(%s, %s, %s)",                                  
            #                           SMS.CATEGORY.SEND, end_time, city.id)      
            mt_sms = self.mysql_db.get("SELECT count(T_SMS_LOG.id) as total"
                                       "  FROM T_SMS_LOG"
                                       "  WHERE T_SMS_LOG.category = %s"
                                       "  AND fetchtime <= %s"
                                       "  AND T_SMS_LOG.mobile IN %s",
                                       SMS.CATEGORY.SEND, end_time, 
                                       tuple(mobiles + DUMMY_IDS))
            # customer, schedule and realtiem call the same procedure
            #custom = self.mysql_db.get("SELECT count(*) as total"
            #                           " FROM T_LOCATION, T_LBMP_TERMINAL, T_XXT_TARGET, T_XXT_GROUP"
            #                           " WHERE category = %s"
            #                           " AND T_LOCATION.timestamp <= %s"
            #                           " AND T_LOCATION.sim = T_LBMP_TERMINAL.sim"
            #                           " AND T_LBMP_TERMINAL.sim = T_XXT_TARGET.mobile"
            #                           " AND T_XXT_TARGET.group_id = T_XXT_GROUP.xxt_id"
            #                           " AND T_XXT_GROUP.city_id = %s",
            #                           LOCATION.CATEGORY.CUSTOM, end_time, city.id)
            #custom = self.mysql_db.get("call P_DAILY_CUSTOM(%s, %s, %s)",
            #                           LOCATION.CATEGORY.CUSTOM, end_time, city.id)
            #schedule = self.mysql_db.get("SELECT count(*) as total"
            #                             " FROM T_LOCATION, T_LBMP_TERMINAL, T_XXT_TARGET, T_XXT_GROUP"
            #                             " WHERE category = %s"
            #                             " AND T_LOCATION.timestamp <= %s"
            #                             " AND T_LOCATION.sim = T_LBMP_TERMINAL.sim"
            #                             " AND T_LBMP_TERMINAL.sim = T_XXT_TARGET.mobile"
            #                             " AND T_XXT_TARGET.group_id = T_XXT_GROUP.xxt_id"
            #                             " AND T_XXT_GROUP.city_id = %s",
            #                             LOCATION.CATEGORY.SCHEDULE, end_time, city.id)
            schedule = self.mysql_db.get("call P_DAILY_CUSTOM(%s, %s, %s)",
                                         LOCATION.CATEGORY.SCHEDULE, end_time, city.id) 
            #realtime= self.mysql_db.get("SELECT count(*) as total"
            #                            " FROM T_LOCATION, T_LBMP_TERMINAL, T_XXT_TARGET, T_XXT_GROUP"
            #                            " WHERE category = %s"
            #                            " AND T_LOCATION.timestamp <= %s"
            #                            " AND T_LOCATION.sim = T_LBMP_TERMINAL.sim"
            #                            " AND T_LBMP_TERMINAL.sim = T_XXT_TARGET.mobile"
            #                            " AND T_XXT_TARGET.group_id = T_XXT_GROUP.xxt_id"
            #                            " AND T_XXT_GROUP.city_id = %s",
            #                            LOCATION.CATEGORY.REALTIME, end_time, city.id)
            realtime = self.mysql_db.get("call P_DAILY_CUSTOM(%s, %s, %s)",
                                         LOCATION.CATEGORY.REALTIME, end_time, city.id)    
            #bound = self.mysql_db.get("SELECT count(*) as total"
            #                          " FROM T_LOCATION, T_LBMP_TERMINAL, T_XXT_TARGET, T_XXT_GROUP"
            #                          " WHERE (category = %s OR category = %s)"
            #                          " AND T_LOCATION.timestamp <= %s"
            #                          " AND T_LOCATION.sim = T_LBMP_TERMINAL.sim"
            #                          " AND T_LBMP_TERMINAL.sim = T_XXT_TARGET.mobile"
            #                          " AND T_XXT_TARGET.group_id = T_XXT_GROUP.xxt_id"
            #                          " AND T_XXT_GROUP.city_id = %s",
            #                          LOCATION.CATEGORY.REGION_ENTER, LOCATION.CATEGORY.REGION_OUT,
            #                          end_time, city.id)
            bound = self.mysql_db.get("call P_DAILY_BOUND(%s, %s, %s, %s)",
                                      LOCATION.CATEGORY.REGION_ENTER, LOCATION.CATEGORY.REGION_OUT, end_time, city.id)  
            #power = self.mysql_db.get("SELECT count(*) as total"
            #                          " FROM T_LOCATION, T_LBMP_TERMINAL, T_XXT_TARGET, T_XXT_GROUP"
            #                          " WHERE category = %s"
            #                          " AND T_LOCATION.timestamp <= %s"
            #                          " AND T_LOCATION.targesimt_id = T_LBMP_TERMINAL.sim"
            #                          " AND T_LBMP_TERMINAL.sim = T_XXT_TARGET.mobile"
            #                          " AND T_XXT_TARGET.group_id = T_XXT_GROUP.xxt_id"
            #                          " AND T_XXT_GROUP.city_id = %s",
            #                          LOCATION.CATEGORY.POWERLOW, end_time, city.id)
            power = self.mysql_db.get("call P_DAILY_POWER(%s, %s, %s)",
                                      LOCATION.CATEGORY.POWERLOW, end_time, city.id)
            #sos = self.mysql_db.get("SELECT count(*) as total"
            #                        " FROM T_LOCATION, T_LBMP_TERMINAL, T_XXT_TARGET, T_XXT_GROUP"
            #                        " WHERE category = %s"
            #                        " AND T_LOCATION.timestamp <= %s"
            #                        " AND T_LOCATION.sim = T_LBMP_TERMINAL.sim"
            #                        " AND T_LBMP_TERMINAL.sim = T_XXT_TARGET.mobile"
            #                        " AND T_XXT_TARGET.group_id = T_XXT_GROUP.xxt_id"
            #                        " AND T_XXT_GROUP.city_id = %s",
            #                        LOCATION.CATEGORY.EMERGENCY, end_time, city.id)
            sos = self.mysql_db.get("call P_DAILY_SOS(%s, %s, %s)",
                                    LOCATION.CATEGORY.EMERGENCY, end_time, city.id) 

            # NOTE: query old_data from mongodb, then add the increment value in past
            # day: schedule, realtime, bound, sos, power
            old_daily = self.collection.find_one({'timestamp': end_time - 86400000}, {'_id':0}) 

            #custom_total = DotDict(old_daily).custom if old_daily else 0
            schedule_total = DotDict(old_daily).schedule if old_daily else 0
            realtime_total = DotDict(old_daily).realtime if old_daily else 0
            bound_total = DotDict(old_daily).bound if old_daily else 0
            sos_total = DotDict(old_daily).sos if old_daily else 0
            power_total = DotDict(old_daily).power if old_daily else 0

            res = {'_id': None,
                   'province_id': city.p_id,
                   'city_id': city.id,
                   'province': city.p_name,
                   'city': city.name,
                   'total_groups': total_groups.total,
                   'total_parents': total_parents.total,
                   'total_children': total_children.total,
                   'mt_sms': mt_sms.total,
                   'mo_sms': mo_sms.total,
                   # total = new + new + ... + new
                   #'custom': custom.total + custom_total,
                   'schedule': schedule.total + schedule_total,
                   'realtime': realtime.total + realtime_total,
                   'bound': bound.total + bound_total,
                   'sos': sos.total + sos_total,
                   'power': power.total + power_total,

                   'timestamp': end_time}

            results.append(res)
        return results

class MDaily(MDailyMixin):
    """This class mainly retrieves data from MySQL as intermediate result
       and stores them into MongoDB.
    """
    def __init__(self):
        MDailyMixin.__init__(self)
        try:
            self.collection.ensure_index([('city_id', pymongo.ASCENDING),
                                          ('timestamp', pymongo.DESCENDING)])
        except:
            logging.exception('mongodb connected failed')

    def retrieve(self, city_list=None, end_time=None):
        """core for Retrieving and Storing operation."""

        """This method returns the last day"""
        if not end_time:
            d = datetime.datetime.fromtimestamp(time.time())
            t = datetime.datetime.combine(datetime.date(d.year, d.month, d.day), datetime.time(0, 0))
            # get today 0:00:00
            end_time = int(time.mktime(t.timetuple())*1000)

        if not city_list:
            cities = self.mysql_db.query("SELECT DISTINCT region_code AS id FROM T_HLR_CITY")
            city_list = [city.id for city in cities]

        results = self.retrieve_mixin(city_list, end_time)
        try:
            for result in results:
                result = DotDict(result)
                query_term = {'city_id': result.city_id, 'timestamp': result.timestamp}
                oldresult = self.collection.find_one(query_term)
                if oldresult:
                    result['_id'] = oldresult['_id']
                else:
                    result.pop('_id')
                self.collection.save(result)
        except Exception as e:
            logging.exception('mongodb saved failed. Error: %s', e.args)
        return results

def main():
    ConfHelper.load('../../../conf/global.conf')
    ins = MDaily()
    ins.retrieve()

if __name__ == "__main__":
    main()
