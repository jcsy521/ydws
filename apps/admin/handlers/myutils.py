# -*- coding:utf-8 -*-

import time, datetime
from dateutil.relativedelta import relativedelta

from utils.misc import DUMMY_IDS
from utils.dotdict import DotDict

def city_list(provinces, db):
    """
    Get a list of cities.
    @return [id1, id2, ...]
    """

    if not provinces:
        return []

    if len(provinces) == 1 and provinces[0] == '0':
        cities = db.query("SELECT region_code FROM T_HLR_CITY")
    else:
        cities = db.query("SELECT region_code FROM T_HLR_CITY"
                          "  WHERE province_id in %s",
                          tuple([int(p) for p in provinces] + DUMMY_IDS))
    city_list = [city.id for city in cities]
    return city_list

def end_of_month(timestamp):
    """
    Return the timestamp that represents the last second of current month.
    This is to say, one second past of the timestamp is the next month.

    @param timestamp: the first millisecond of the current month.

    @return the first utc of the next month
    """
    current_day = datetime.datetime.fromtimestamp(timestamp/1000)
    # make sure the first second of the next month.
    day_ = current_day + relativedelta(months=1,
                                       day=1, hour=0, minute=0, second=0)
    epoch = (int(time.mktime(day_.timetuple())) - 1) * 1000
    return epoch

def start_of_month(timestamp):
    """
    Return the timestamp that represents the last second of current month.
    This is to say, one second past of the timestamp is the next month.

    @param timestamp: the first millisecond of the current month.

    @return the first utc of the next month
    """
    current_day = datetime.datetime.fromtimestamp(timestamp/1000)
    # make sure the first second of the next month.
    day_ = current_day + relativedelta(months=0,
                                       day=1, hour=0, minute=0, second=0)
    epoch = (int(time.mktime(day_.timetuple()))) * 1000
    return epoch

def start_end_of_month():
    """
    get start and end time of the month which last day is within

    @return the start_time and end_time of the month
    """
    # snippet is executed after 0:00:00
    # get yesterday 23:59:59
    d = datetime.datetime.fromtimestamp(time.time())
    daydelta = datetime.date(d.year, d.month, d.day) - datetime.timedelta(days=1)
    t = datetime.datetime.combine(daydelta, datetime.time(23, 59, 59))
    end_time = int(time.mktime(t.timetuple())) * 1000
    #get the first day of the month 
    d = datetime.datetime.fromtimestamp(end_time/1000)
    t = datetime.datetime.combine(datetime.date(d.year,d.month, 1), datetime.time(0, 0))
    start_time = int(time.mktime(t.timetuple())) * 1000
    return start_time, end_time

def city_info(city_list, db):
    """
    get all info of a city
    @param city_list: [id1, id2]
    @return cities: id, name, p_id, p_name
    """
    cities = [] 
    for city in city_list:
        res = db.query("SELECT thp.province_id AS p_id, thp.province_name AS p_name,"
                       "       thc.city_name AS name, thc.region_code AS id"
                       "  FROM T_HLR_CITY AS thc, T_HLR_PROVINCE AS thp"
                       "  WHERE thc.region_code = %s"
                       "    AND thc.province_id = thp.province_id",
                       city)
        for r in res: 
            c = DotDict({'id':r.id, 'name':r.name, 'p_id':r.p_id, 'p_name':r.p_name})
            cities.append(c)
    return cities
