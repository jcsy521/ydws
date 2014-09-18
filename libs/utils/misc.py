# -*- coding: utf-8 -*-

import time
import datetime
from dateutil.relativedelta import relativedelta
import functools
import random
import math
import hashlib
import os

# import some modules for VG
from dotdict import DotDict

# all SQL DELETE in http.delete request use IN to match ids,
# therefore, if there were only on or none ids in the request, the SQL
# will be illegal (e.g., tuple([1]) --> (1,), which is wrong for SQL
# IN (1,). I set the dummy_ids to be appended with all ids to make it safe. 
DUMMY_IDS = [-2, -2]
DUMMY_IDS_STR = ['-2', '-2']

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
    return str("register_captcha:%s" % umobile)

def get_ios_id_key(umobile):
    """for the ios id of ios."""
    return str("ios_id:%s" % umobile)

def get_ios_badge_key(umobile):
    """for the ios badge of ios."""
    return str("ios_badge:%s" % umobile)

def get_ios_push_list_key(uid): 
    """for the iosid_lst of IOS"""
    return str("ios_push_list:%s" % uid)  

def get_android_push_list_key(uid): 
    """for the devid_lst of Android."""
    return str("android_push_list:%s" % uid) 

def get_lastinfo_key(umobile):
    """for the newest lastinfo of owner"""
    return str("lastinfo:%s" % umobile)

def get_lastinfo_time_key(umobile):
    """for the newest lastinfo of owner"""
    return str("lastinfo_time:%s" % umobile)

def get_lastposition_key(umobile):
    """for the newest lastposition of owner"""
    return str("lastposition:%s" % umobile)

def get_lastposition_time_key(umobile):
    """for the newest lastposition of owner"""
    return str("lastposition_time:%s" % umobile)

def get_lastinfo_line_key(line_id):
    """for the newest lastinfo of line"""
    return str("lastinfo_line:%s" % line_id)

def get_lastinfo_line_time_key(line_id):
    """for the newest lastinfo of line"""
    return str("lastinfo_line_time:%s" % line_id)

def get_location_key(dev_id):
    """for the newest location of dev"""
    return str("location:%s" % dev_id)

def get_gps_location_key(dev_id):
    """for the newest gps location of dev"""
    return str("gps_location:%s" % dev_id)

def get_region_status_key(dev_id, region_id):
    """for the newest region status of dev"""
    return str("region_status:%s%s" % (dev_id, region_id))

def get_region_time_key(dev_id, region_id):
    """for the newest region event's time of dev"""
    return str("region_time:%s%s" % (dev_id, region_id))

def get_single_status_key(dev_id, single_id):
    """for the newest single status of dev"""
    return str("single_status:%s%s" % (dev_id, single_id))

def get_single_time_key(dev_id, single_id):
    """for the newest single event's time of dev"""
    return str("single_time:%s%s" % (dev_id, single_id))

def get_terminal_sessionID_key(dev_id):
    return str("sessionID:%s" % dev_id)

def get_terminal_address_key(dev_id):
    return str("terminal_address:%s" % dev_id)

def get_location_cache_key(lon, lat):
    """save name, Generate location (lon, lat)'s memechached key."""
    return "lk:%d:%d" % (lon/100, lat/100)

def get_terminal_info_key(dev_id):
    return str("terminal_info:%s" % (dev_id))

def get_alarm_info_key(dev_id):
    return str("alarm_info:%s" % (dev_id))

def get_lqgz_key(dev_id):
    return str("lqgz:%s" % dev_id)

def get_kqly_key(dev_id):
    return str("kqly:%s" % dev_id)

def get_lqgz_interval_key(dev_id):
    return str("lqgz_interval:%s" % dev_id)

def get_lq_sms_key(dev_id):
    return str("lq:%s" % dev_id)

def get_lq_interval_key(dev_id):
    return str("lq_interval:%s" % dev_id)

def get_offline_lq_key(dev_id):
    return str("offline_lq:%s" % dev_id)

def get_agps_data_key(key):
    return str("agps_data:%s" % key)

def get_resend_key(dev_id, timestamp, command):
    return str("resend:%s%s%s" % (dev_id, timestamp, command))

def get_power_full_key(dev_id):
    return str("power_full:%s" % dev_id)

def get_del_data_key(dev_id):
    return str("del_data:%s" % dev_id)

def get_login_time_key(dev_id):
    return str("login_time:%s" % dev_id)

def get_track_key(dev_id):  
    return str("track:%s" % dev_id) 

def get_alert_freq_key(dev_id):
    return str("alert_freq:%s" % dev_id)    

def get_pbat_message_key(dev_id):
    return str("pbat_message:%s" % dev_id)

def get_mileage_key(dev_id):
    return str("mileage:%s" % dev_id)

def get_avatar_time_key(tid):
    """for the last modified time of the avatar belongs to the tid"""
    return str("avatar_time:%s" % tid)

def get_corp_info_key(cid):
    """for the corp"""
    return str("corpinfo:%s" % cid)

def get_group_info_key(cid):
    """for the group belongs to cid"""
    return str("groupinfo:%s" % cid)

def get_group_terminal_info_key(cid, gid):
    """for the terminals belongs to cid, gid"""
    return str("terminalinfo:%s:%s" % (cid, gid))

def get_group_terminal_detail_key(cid, gid, tid):
    """for the terminal detail belongs to cid, gid"""
    return str("terminaldetail:%s:%s:%s" % (cid, gid, tid))

def get_acc_status_info_key(tid):
    """for the acc_status info belongs to the tid"""
    return str("acc_status_info:%s" % tid)

def get_speed_limit_key(tid):
    """for the speed_limit associated with the tid"""
    return str("speed_limit:%s" % tid)

def get_stop_key(tid):
    """for the stop_point associated with the tid"""
    return str("stop:%s" % tid)

def get_distance_key(tid):
    """for the distance associated with the tid"""
    return str("distance:%s" % tid)

def get_last_pvt_key(tid):
    """for the last pvt associated with the tid"""
    return str("last_pvt:%s" % tid)

def get_terminal_time(timestamp):
    """Format a readable time like 2013-10-10，10:10:10 
    """
    terminal_time = ""
    try:
        from datetime import datetime
        terminal_time = datetime.fromtimestamp(int(timestamp)).strftime("%Y-%m-%d，%H:%M:%S")
    except:
        terminal_time = time.strftime("%Y-%m-%d，%H:%M:%S")
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
    """convert a list to a string.
    """
    s = ''
    for i in list:
        s += str(i)

    return s

def utc_to_date(timestamp):
    """Get a readable date through a utc time.
    """
    if not timestamp:
        return ''
    else:
        return time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(timestamp))

def seconds_to_label(seconds):
    """Get a label like '1天4时20分' through some seconds.
    """
    label = ''
    if not seconds:
        pass
    elif int(seconds) < 0:
        pass
    else:
        _minute = int(round(float(seconds)/60))
        if _minute >= 60:
            _hour = int(math.floor(float(_minute)/60))
            _minute = _minute % 60
            if _hour >= 24: 
                _day = int(math.floor(float(_hour)/24))
                _hour = _hour % 24 
                label += u'%s天' % _day
            label += u'%s时' % _hour
        label += u'%s分' % _minute
    return label

def get_sessionID():
    """Get a random str with lengh 8 as a sessionID.
    """
    sessionID = ''
    base_str = 'abcdefghijklmnopqrstuvwxyz0123456789'
    for i in range(8):
        index = random.randint(0, 35)
        sessionID += base_str[index]

    return sessionID

def get_psd():
    """Get a random digit with lengh 6 as a password.
    """
    psd = ''
    base_str = '0123456789'
    for i in range(6):
        index = random.randint(0, 9)
        psd += base_str[index]

    return psd 

def get_activation_code():
    """A string consist of digits and upercase, whose length is 10.  
    Do not include number 0,1 and letter o,i,l.  
    """ 
    activation_code = '' 
    base_str = '23456789ABCDEFGHJKMNPQRSTUVWXYZ' 
    activation_code = ''.join(random.choice(base_str) for x in range(10)) 
    return activation_code

def start_end_of_year(year="2011"):
    """Get start and end time of the year.
    """
    timestamp = int(time.mktime(time.strptime("%s"%year,"%Y")))    
    current_day = datetime.datetime.fromtimestamp(timestamp)    
    s = current_day + relativedelta(months=0, day=1, hour=0, minute=0, second=0)    
    e = current_day + relativedelta(months=12, day=1, hour=0, minute=0, second=0)
    s_epoch = int(time.mktime(s.timetuple()))
    e_epoch = int(time.mktime(e.timetuple())-1)
    return s_epoch, e_epoch

def start_end_of_month(year="2012",month="11"):
    """Get start and end time of the month which is in the year.
    """
    timestamp = int(time.mktime(time.strptime("%s-%s"%(year,month),"%Y-%m")))    
    current_day = datetime.datetime.fromtimestamp(timestamp)    
    s = current_day + relativedelta(months=0, day=1, hour=0, minute=0, second=0)    
    e = current_day + relativedelta(months=1, day=1, hour=0, minute=0, second=0)
    s_epoch = int(time.mktime(s.timetuple()))
    e_epoch = int(time.mktime(e.timetuple())-1)
    return s_epoch, e_epoch

def start_end_of_day(year="2012",month="11",day="1"):
    """Get start and end time of the day which is in the year, month and day.
    """
    timestamp = int(time.mktime(time.strptime("%s-%s-%s"%(year,month,day),"%Y-%m-%d")))    
    current_day = datetime.datetime.fromtimestamp(timestamp)    
    s = current_day + relativedelta(months=0, day=0, hour=0, minute=0, second=0)    
    s_epoch = int(time.mktime(s.timetuple()))
    e_epoch = s_epoch + 24*60*60 - 1
    return s_epoch, e_epoch

def start_end_of_quarter(year="2012",quarter="1"):
    """Get start and end time of the quarter which is in the year.
    """
    months = {'1':[1,3],
              '2':[4,6],
              '3':[7,9],
              '4':[10,12]}
    month = months[quarter]
    s_epoch = int(time.mktime(time.strptime("%s-%s"%(year,month[0]),"%Y-%m")))

    e_epoch = int(time.mktime(time.strptime("%s-%s"%(year,month[1]),"%Y-%m")))
    current_day = datetime.datetime.fromtimestamp(e_epoch)
    day_ = current_day + relativedelta(months=1,
                                       day=1, hour=0, minute=0, second=0)
    e_epoch = (int(time.mktime(day_.timetuple())) - 1)    
    return s_epoch, e_epoch

def days_of_month(year="2012",month="11"):
    """Get the number of days which is in the year and month.
    """
    timestamp = int(time.mktime(time.strptime("%s-%s"%(year,month),"%Y-%m")))    
    current_day = datetime.datetime.fromtimestamp(timestamp)    
    e = current_day + relativedelta(months=1, day=1, hour=0, minute=0, second=0)
    e_epoch = int(time.mktime(e.timetuple())-1)
    days = datetime.datetime.fromtimestamp(e_epoch).day
    return days

def get_date_from_utc(timestamp):
    """Get a readable data from utc time.
    @params: timestamp, utc, in second, for instance, 1373278897
    @return: year, 
             month, 
             day,
             hour,
             minute,
             second,
    """
    date = time.localtime(timestamp)
    year, month, day, hour, minute, second = date.tm_year, date.tm_mon, date.tm_mday, date.tm_hour, date.tm_min, date.tm_sec
    return DotDict(year=year, 
                   month=month, 
                   day=day, 
                   hour=hour,
                   minute=minute, 
                   second=second)

def get_tid_from_mobile_ydwq(mobile):
    """Get tid according tid in ydwq.
    """
    #tid = ''
    #if mobile:
    #    tid = mobile[::-1]

    tid = mobile
    return tid

def get_md5(body): 
    m = hashlib.md5() 
    m.update(body) 
    md5 = m.hexdigest() 
    return md5

def visitor(lst, directoryName, filesInDirectory): 
    """Get md5 from all *.js and .css.
    """
    if ".svn" in directoryName:
        return
    for fname in filesInDirectory:
        if not(fname.endswith(".js") or fname.endswith(".css")):
            continue
        fpath = os.path.join(directoryName, fname)
        if not os.path.isdir(fpath):
            bytes=open(fpath, 'rb').read()
            md5 = get_md5(bytes)
            lst.append(md5)

def get_static_hash(path):
    lst = []
    os.path.walk(path, visitor, lst)
    body = ''.join(lst)
    return get_md5(body)
    

if __name__ == '__main__':
    #For Test
    psd = get_psd()
    print 'psd', psd
    
