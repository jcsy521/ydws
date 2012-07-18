#! /usr/bin/enb/python
# -*- coding:utf-8 -*-

import logging
import os.path
import site

TOP_DIR_ = os.path.abspath(os.path.join(__file__, "../../../.."))
site.addsitedir(os.path.join(TOP_DIR_, "libs"))

TOP_DIR_ = os.path.abspath(os.path.join(__file__, "../../handlers"))
site.addsitedir(TOP_DIR_)

import pymongo

from db_.mysql import DBConnection
from db_.mongodb import MongoDBConnection
from constants import XXT
from utils.dotdict import DotDict

from helpers.confhelper import ConfHelper

class MGroupMixin(object):

    def __init__(self):
        self.mysql_db = DBConnection().db

    def retrieve_mixin(self, citylist=None):
        results = []
        for city in citylist:
            infos = self.mysql_db.query("SELECT thp.province_id AS id, thp.province_name AS province_name,"
                                        "       thc.city_name AS city_name"
                                        "  FROM T_HLR_CITY AS thc, T_HLR_PROVINCE AS thp"
                                        "  WHERE thc.region_code = %s"
                                        "    AND thc.province_id = thp.province_id", city)
            for info in infos:
                groups = self.mysql_db.query("SELECT txg.id, txg.xxt_id, txg.name,"
                                             " txa.xxt_id AS agency_id, txa.name AS agency_name"
                                             " FROM T_XXT_GROUP AS txg LEFT JOIN T_XXT_AGENCY AS txa"
                                             "   ON txa.xxt_id = txg.agency_id"
                                             " WHERE txg.city_id = %s", city)
                for group in groups:
                    #total_parents = self.mysql_db.get("SELECT count(*) AS total"
                    #                                  " FROM T_XXT_USER AS txu"
                    #                                  " WHERE txu.group_id = %s", group.xxt_id)
                    total_parents = self.mysql_db.get("call P_GROUP_TOTAL_PARENTS(%s)",
                                                      group.xxt_id) 
                    #total_children = self.mysql_db.get("SELECT count(*) AS total"
                    #                                   " FROM T_XXT_TARGET AS txt"
                    #                                   " WHERE txt.group_id = %s", group.xxt_id)
                    total_children = self.mysql_db.get("call P_GROUP_TOTAL_CHILDREN(%s)",
                                                       group.xxt_id) 
                    if not group.agency_name:
                        group.agency_name = u'暂无'

                    res = {'_id': None,
                           'province_id': info.id,
                           'city_id': city,
                           'id': group.id,
                           'group_id': group.xxt_id,
                           'group_name': group.name,
                           'agency_id': group.agency_id,
                           'agency': group.agency_name,
                           'total_parents': total_parents.total,
                           'total_children': total_children.total,
                           'city': info.city_name,
                           'province': info.province_name}
                    results.append(res)
        return results
  
class MGroup(MGroupMixin):
    """This class mainly retrieves information about group from MySQL
       as intermediate result and stores them into MongoDB.
    """
    def __init__(self):
        MGroupMixin.__init__(self)
        try:
            self.mongodb_db = MongoDBConnection().db
            self.collection = self.mongodb_db.groups
            self.collection.ensure_index([('city_id', pymongo.ASCENDING),
                                          ('group_id', pymongo.ASCENDING),
                                          ('agency_id', pymongo.ASCENDING)])
        except:
            logging.exception('mongodb connected failed')
    def retrieve(self, citylist=None):
        """core for Retrieving and Storing operation."""
        #store the complete data of curent month into MongoDB
        if not citylist:
            cities = self.mysql_db.query("SELECT DISTINCT region_code AS id"
                                         "  FROM T_HLR_CITY")
            citylist = [c.id for c in cities]

        results = self.retrieve_mixin(citylist)

        # get the group_id list from mongodb(may include the group_id has been removed)
        res = self.collection.find({'city_id': { '$in' : citylist }}, {'group_id':1})
        ids_mongod = [int(v['group_id']) for v in res]
        # get the group_id lsit from mysql (the latest)
        ids_mysql = [int(result['group_id']) for result in results]        
        # get the group_id to be removed and remove them from mongodb
        ids_move = list(set(ids_mongod) - set(ids_mysql))
        self.collection.remove({'group_id': {'$in':ids_move}})

        try:
            for result in results:
                result = DotDict(result)
                oldresult = self.collection.find_one({'id': result.id})
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
    ins = MGroup()
    ins.retrieve()

if __name__ == "__main__":
    main()
