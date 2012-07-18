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

import pymongo

from db_.mysql import DBConnection
from db_.mongodb import MongoDBConnection
from utils.dotdict import DotDict
from myutils import city_info
from helpers.confhelper import ConfHelper
from utils.misc import DUMMY_IDS

class MSmsMixin(object):

    def __init__(self):
        self.mysql_db = DBConnection().db
 
    def retrieve_mixin(self, city_list=None, start_time=None, end_time=None):
        # this is for parents
        #res = self.mysql_db.query("SELECT tsl.mobile, tsl.fetchtime, txu.name AS user_name,"
        #                          "       txg.xxt_id AS group_id, txg.name AS group_name,"
        #                          "       thc.region_code AS city_id, thc.city_name AS city,"
        #                          "       thp.province_id AS province_id, thp.province_name AS province"
        #                          " FROM T_SMS_LOG AS tsl, T_XXT_USER AS txu,"
        #                          "      T_XXT_GROUP AS txg, T_HLR_CITY AS thc,"
        #                          "      T_HLR_PROVINCE AS thp"
        #                          " WHERE tsl.fetchtime BETWEEN %s AND %s"
        #                          " AND tsl.mobile = txu.mobile"
        #                          " AND txu.group_id = txg.xxt_id"
        #                          " AND txg.city_id = thc.region_code"
        #                          " AND thc.province_id = thp.province_id",
        #                          start_time, end_time) 
        results = []
        cities = city_info(city_list, self.mysql_db)
        for city in cities:
            #res_parents = self.mysql_db.query("call P_SMS_PARENTS(%s, %s, %s)",
            #                                  start_time, end_time, city.id)

            sms_pres_parent = self.mysql_db.query("SELECT DISTINCT txu.mobile, txu.name AS user_name, "
                                   "  txg.xxt_id AS group_id, txg.name AS group_name,"
                                   "  thc.region_code AS city_id, thc.city_name AS city,"
                                   "  thp.province_id AS province_id, thp.province_name AS province" 
                                   "  FROM T_XXT_USER AS txu,"
                                   "      T_XXT_GROUP AS txg," 
                                   "      T_HLR_CITY AS thc,"
                                   "      T_HLR_PROVINCE AS thp"
                                   "  WHERE txu.group_id = txg.xxt_id "
                                   "  AND txg.city_id = thc.region_code"
                                   "  AND thc.province_id = thp.province_id"
                                   "  AND txg.city_id = %s",
                                   city.id)
            res_parents = [] 
            for sms_pre in sms_pres_parent:
                sms_parents = self.mysql_db.query("SELECT mobile, fetchtime"
                                                  "  FROM T_SMS_LOG"
                                                  "  where fetchtime BETWEEN %s AND %s"
                                                  "  AND mobile = %s",
                                                  start_time, end_time,
                                                  sms_pre.mobile)
                for sms_parent in sms_parents:
                    res_parent = DotDict({'mobile':sms_parent.mobile,
                                  'fetchtime':sms_parent.fetchtime,
                                  'user_name':sms_pre.user_name,
                                  'group_id':sms_pre.group_id,
                                  'group_name':sms_pre.group_name,
                                  'city_id':sms_pre.city_id,
                                  'city':sms_pre.city,
                                  'province_id':sms_pre.province_id,
                                  'province':sms_pre.province}) 
                    res_parents.append(res_parent)
                
            results.extend(res_parents)
        #this is for targets
        #res = self.mysql_db.query("SELECT tsl.mobile, tsl.fetchtime, txt.name AS user_name,"
        #                          "       txg.xxt_id AS group_id, txg.name AS group_name,"
        #                          "       thc.region_code AS city_id, thc.city_name AS city,"
        #                          "       thp.province_id AS province_id, thp.province_name AS province"
        #                          " FROM T_SMS_LOG AS tsl, T_XXT_TARGET AS txt,"
        #                          "      T_XXT_GROUP AS txg, T_HLR_CITY AS thc,"
        #                          "      T_HLR_PROVINCE AS thp"
        #                          " WHERE tsl.fetchtime BETWEEN %s AND %s"
        #                          " AND tsl.mobile = txt.mobile"
        #                          " AND txt.group_id = txg.xxt_id"
        #                          " AND txg.city_id = thc.region_code"
        #                          " AND thc.province_id = thp.province_id",
        #                          start_time, end_time) 
        #    res_targets = self.mysql_db.query("call P_SMS_TARGETS(%s, %s, %s)",
        #                                      start_time, end_time, city.id)

            sms_pres_target = self.mysql_db.query("SELECT DISTINCT txt.mobile, txt.name AS user_name, "
                                   "  txg.xxt_id AS group_id, txg.name AS group_name,"
                                   "  thc.region_code AS city_id, thc.city_name AS city,"
                                   "  thp.province_id AS province_id, thp.province_name AS province" 
                                   "  FROM T_XXT_TARGET AS txt,"
                                   "      T_XXT_GROUP AS txg," 
                                   "      T_HLR_CITY AS thc,"
                                   "      T_HLR_PROVINCE AS thp"
                                   "  WHERE txt.group_id = txg.xxt_id "
                                   "  AND txg.city_id = thc.region_code"
                                   "  AND thc.province_id = thp.province_id"
                                   "  AND txg.city_id = %s",
                                   city.id)
            res_targets = [] 
            for sms_pre in sms_pres_target:
                sms_targets = self.mysql_db.query("SELECT mobile, fetchtime"
                                                  "  FROM T_SMS_LOG"
                                                  "  WHERE fetchtime BETWEEN %s AND %s"
                                                  "  AND mobile = %s",
                                                  start_time, end_time,
                                                  sms_pre.mobile)
                for sms_target in sms_targets:
                    res_target = DotDict({'mobile':sms_target.mobile,
                                  'fetchtime':sms_target.fetchtime,
                                  'user_name':sms_pre.user_name,
                                  'group_id':sms_pre.group_id,
                                  'group_name':sms_pre.group_name,
                                  'city_id':sms_pre.city_id,
                                  'city':sms_pre.city,
                                  'province_id':sms_pre.province_id,
                                  'province':sms_pre.province}) 
                    res_targets.append(res_target)
            results.extend(res_targets)
        return results 
         
    def distinct(self, results):
        """recount the result, provide for frontend""" 
        res = []
        mobiles = [r['mobile'] for r in results]
        d_mobiles = list(set([r['mobile'] for r in results]))
        for mobile in d_mobiles:
            for result in results:
                if mobile == result['mobile']:
                    count = mobiles.count(mobile)
                    r = {'province':result['province'],
                         'city':result['city'],
                         'mobile':mobile,
                         'count':count,
                         'group_name':result['group_name'],
                         'group_id':result['group_id'],
                         'user_name':result['user_name']}
                    res.append(r)
                    break
        return res
   
class MSms(MSmsMixin):
    """This class mainly retrieves sms information from MySQL
    as intermediate result and stores them into MongoDB.
    """
    def __init__(self):
        MSmsMixin.__init__(self)
        try:
            self.mongodb_db = MongoDBConnection().db
            self.collection = self.mongodb_db.sms
            self.collection.ensure_index([('city_id', pymongo.ASCENDING),
                                          ('group_id', pymongo.ASCENDING),
                                          ('fetchtime', pymongo.DESCENDING)])
        except:
            logging.exception('mongodb connected failed')
        
    def retrieve(self, city_list=None, start_time=None, end_time=None):
        """only retrieve data of last day."""
        if not (start_time and end_time):
            d = datetime.datetime.fromtimestamp(time.time())
            daydelta = datetime.date(d.year, d.month, d.day) - datetime.timedelta(days=1)
            t = datetime.datetime.combine(daydelta, datetime.time(0, 0))
            start_time = time.mktime(t.timetuple())*1000
            t = datetime.datetime.combine(datetime.date(d.year, d.month, d.day), datetime.time(0, 0))
            end_time = time.mktime(t.timetuple())*1000

        if not city_list:
            cities = self.mysql_db.query("SELECT DISTINCT region_code AS id FROM T_HLR_CITY")
            city_list = [city.id for city in cities]

        results = self.retrieve_mixin(city_list, start_time, end_time)
        try:
            for result in results:
                query_term = {'mobile': result.mobile, 'fetchtime': result.fetchtime}
                oldresult = self.collection.find_one(query_term)
                res = {'_id': None,
                       'mobile': result.mobile,
                       'fetchtime': result.fetchtime,
                       'user_name': result.user_name,
                       'group_id': result.group_id,
                       'group_name': result.group_name,
                       'city_id': result.city_id,
                       'city': result.city,
                       'province_id': result.province_id,
                       'province': result.province}
                if oldresult:
                    res['_id'] = oldresult['_id']
                else:
                    res.pop('_id')
                self.collection.save(res)
        except Exception as e:
            logging.exception('mongodb saved failed. Error: %s', e.args)
        # get the result requried by frontend
        results = self.distinct(results)
        return results

def main():
    ConfHelper.load('../../../conf/global.conf')
    ins = MSms()
    ins.retrieve()

if __name__ == "__main__":
    main()
