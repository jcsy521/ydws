# -*- coding: utf-8 -*-

import time
import datetime
from dateutil.relativedelta import relativedelta
import functools
import random

# import some modules for VG
from dotdict import DotDict

# all SQL DELETE in http.delete request use IN to match ids,
# therefore, if there were only on or none ids in the request, the SQL
# will be illegal (e.g., tuple([1]) --> (1,), which is wrong for SQL
# IN (1,). I set the dummy_ids to be appended with all ids to make it safe. 
DUMMY_IDS = [-1, -1]

def log_time(method):
    """This decorator prints the runnting time of method."""
    @functools.wraps(method)
    def wrapper(*args, **kwargs):
        s = time.time()
        r = method(*args, **kwargs)
        print "<log_time> %s: %d ms" % (method.__name__, (time.time() - s) * 1000)
        return r
    return wrapper

def safe_utf8(s):
    if isinstance(s, unicode):
        return s.encode("utf-8", 'ignore')
    assert isinstance(s, str)
    return s

def safe_unicode(s):
    if isinstance(s, str):
        try:
            s = s.decode("utf-8")
        except:
            try:
                s = s.decode("gbk")
            except:
                # unknow encoding...
                s = u""
    assert isinstance(s, unicode)
    return s

def str_to_list(str_, delimiter=','):
    if not str_:
        return []
    else:
        return str_.replace(delimiter, ' ').split()

def get_captcha_key(umobile):
    """for the captcha of umobile"""
    return str("captcha:%s" % umobile)

def get_location_key(dev_id):
    """for the newest location of dev"""
    return str("location:%s" % dev_id)

def get_terminal_sessionID_key(dev_id):
    return str("sessionID:%s" % dev_id)

def get_terminal_address_key(dev_id):
    return str("terminal_address:%s" % dev_id)

def get_location_cache_key(lon, lat):
    """save name, Generate location (lon, lat)'s memechached key."""
    return "lk:%d:%d" % (lon/100, lat/100)

def get_terminal_info_key(dev_id):
    return str("terminal_info:%s" % (dev_id))

def get_lq_sms_key(dev_id):
    return str("lq:%s" % dev_id)

def get_lq_interval_key(dev_id):
    return str("lq_interval:%s" % dev_id)

def get_agps_data_key(key):
    return str("agps_data:%s" % key)

def get_terminal_time(timestamp):
    terminal_time = ""
    try:
        from datetime import datetime
        terminal_time = datetime.fromtimestamp(int(timestamp)).strftime("%Y-%m-%d %H:%M:%S")
    except:
        terminal_time = time.strftime("%Y-%m-%d %H:%M:%S")
    return terminal_time

def get_today_last_month():
    # use localtime for later time.mktime()
    now_ = datetime.datetime.now()
    # today of the last month
    back_most = now_ + relativedelta(months=-1,
                                     hour=0, minute=0, second=0)
    # mktime needs localtime
    back_most = int(time.mktime(back_most.timetuple()) * 1000)
    return back_most
	
def list_to_str(list):

    s = ''
    for i in list:
        s += str(i)

    return s

def get_sessionID():
    sessionID = ''
    base_str = 'abcdefghijklmnopqrstuvwxyz0123456789'
    for i in range(8):
        index = random.randint(0, 35)
        sessionID += base_str[index]

    return sessionID

def get_psd():
    psd = ''
    base_str = 'abcdefghjkmnpqrstuvwxyz23456789'
    for i in range(6):
        index = random.randint(0, 30)
        psd += base_str[index]

    return psd 
