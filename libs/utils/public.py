# -*- coding: utf-8 -*-

import logging
import time 

from helpers.queryhelper import QueryHelper
from helpers.smshelper import SMSHelper
from helpers.emailhelper import EmailHelper

from misc import *
from utils.dotdict import DotDict
from constants import EVENTER, UWEB, GATEWAY

def record_add_action(tmobile, group_id, add_time, db):
    """Record the add action of one mobile.
    @params: tmobile, 
             group_id, 
             op_type, 
             add_time,
    """
    logging.info("[PUBLIC] Record the add action, tmobile: %s, group_id: %s, add_time: %s",
                 tmobile, group_id, add_time)
    db.execute("INSERT INTO T_BIND_LOG(tmobile, group_id, op_type, add_time)" 
               " VALUES(%s, %s, %s, %s)", 
               tmobile, group_id, UWEB.OP_TYPE.ADD, add_time)              
               
def record_del_action(tmobile, group_id, del_time, db):
    """Record the del action of one mobile.
    @params: tmobile, 
             group_id, 
             op_type, 
             del_time,
    """
    logging.info("[PUBLIC] Record the del action, tmobile: %s, group_id: %s, del_time: %s",
                 tmobile, group_id, del_time)
    db.execute("INSERT INTO T_BIND_LOG(tmobile, group_id, op_type, del_time)" 
               " VALUES(%s, %s, %s, %s)", 
               tmobile, group_id, UWEB.OP_TYPE.DEL, del_time)              

def clear_data(tid, db, redis):
    """Just clear the info associated with terminal in platform.
    """
    terminal = db.get("SELECT mobile, owner_mobile, group_id FROM T_TERMINAL_INFO"
                      "  WHERE tid = %s", tid)
    if not terminal:
        logging.info("Terminal: %s already does not exist, do nothing.", tid)
        return 
    else:
        logging.info("[PUBLIC] Delete db data of terminal: %s", tid)

        # clear db 
        db.execute("DELETE FROM T_LOCATION"
                   "  WHERE tid = %s",
                   tid)

        db.execute("DELETE FROM T_MILEAGE_LOG"
                   "  WHERE tid = %s",
                   tid)

        db.execute("DELETE FROM T_EVENT"
                   " WHERE tid = %s",
                   tid)

        db.execute("DELETE FROM T_STOP"
                   "  WHERE tid = %s",
                   tid)

        db.execute("DELETE FROM T_CHARGE"
                   " WHERE tid = %s",
                   tid)

        db.execute("DELETE FROM T_REGION_TERMINAL"
                   "  WHERE tid = %s",
                   tid)

        db.execute("delete FROM T_REGION_TERMINAL"
                   "  WHERE tid = %s", tid)

        # clear redis
        tmobile = terminal.mobile if terminal else ""
        umobile = terminal.owner_mobile if terminal else None

        keys = []
        if tid:
            tid_keys = redis.keys('*:%s'%tid)
            keys.extend(tid_keys)

        if tmobile:
            tmobile_keys = redis.keys('*:%s'%tmobile)
            keys.extend(tmobile_keys)

        if keys:
            redis.delete(*keys)

        logging.info("[PUBLIC] Delete terminal's keys in reids, tid: %s, tmobile: %s, umobile: %s, keys: %s",
                     tid, tmobile, umobile, keys)

def delete_terminal(tid, db, redis, del_user=True):
    """Delete terminal from platform and clear the associated info.
    """
    terminal = db.get("SELECT mobile, owner_mobile, group_id FROM T_TERMINAL_INFO"
                      "  WHERE tid = %s", tid)
    if not terminal:
        logging.info("Terminal: %s already does not exist, do nothing.", tid)
        return
    else:
        user = db.get("SELECT id FROM T_USER"
                      "  WHERE mobile = %s",
                      terminal.owner_mobile)
        #NOTE: record the del action.
        record_del_action(terminal.mobile, terminal.group_id, int(time.time()), db)

        #NOTE: check whether clear history data
        key = get_del_data_key(tid)
        flag = redis.get(key)
        if flag and int(flag) == 1:
            clear_data(tid, db, redis)
            redis.delete(key)

        #NOTE: delete terminal
        db.execute("DELETE FROM T_TERMINAL_INFO"
                   "  WHERE tid = %s", 
                   tid) 

        logging.info("[PUBLIC] Delete Terminal: %s, tmobile: %s, umobile: %s",
                     tid, tmobile, umobile)

def add_user(user, db, redis):
    """"Add a user.
    @param: user, {'umobie':'', 
                   'password':'',
                   'uname':'',
                   'address':'',
                   'email':''}
    @param: db
    @param: redis

    """
    # add user
    user = db.get("SELECT id FROM T_USER WHERE mobile = %s", user['umobile'])
    if not user:
        db.execute("INSERT INTO T_USER(id, uid, password, name, mobile, address, email, remark)"
                   "  VALUES(NULL, %s, password(%s), %s, %s, %s, %s, NULL)",
                   user['umobile'], user['password'],
                   user['uname'], user['umobile'],
                   user['address'], user['email'])

    # add sms_option
    sms_option = db.get("SELECT id FROM T_SMS_OPTION WHERE uid= %s", user['umobile'])
    if not sms_option:
        db.execute("INSERT INTO T_SMS_OPTION(uid)"
                   "  VALUES(%s)",
                   user['umobile'])

def add_terminal(terminal, db, redis):
    """"Add a terminal.
    @param: terminal, {'tmobile':'', 
                       'owner_mobile':'',
                       'begintime':'',
                       'endtime':'',
                       'offline_time':''}
    @param: db
    @param: redis
    """
    # add terminal
    db.execute("INSERT INTO T_TERMINAL_INFO(tid, mobile, owner_mobile,"
               "  begintime, endtime, offline_time)"
               "  VALUES (%s, %s, %s, %s, %s, %s)",
               terminal['tmobile'],
               terminal['tmobile'], terminal['owner_mobile'],
               terminal['begintime'], terminal['endtime'], fields.begintime)
    
    #add car tnum --> cnum
    db.execute("INSERT INTO T_CAR(tid, cnum, type, color, brand)"
               "  VALUES(%s, %s, %s, %s, %s)",
               terminal['tmobile'], terminal['cnum'], 
               terminal['ctype'], terminal['ccolor'], terminal['cbrand'])
 
def insert_location(location, db, redis):
    """Insert whole-data into T_LOCATION.
    """
    location = DotDict(location)
    #NOTE if locate_error is bigger then 500, set it 500
    if int(location.locate_error) > 500:
        location.locate_error = 500
    lid = db.execute("INSERT INTO T_LOCATION(tid, latitude, longitude, altitude,"
                     "    clatitude, clongitude, timestamp, name, category, type,"
                     "    speed, degree, cellid, locate_error)"
                     "  VALUES (%s, %s, %s, %s, %s, %s, %s,"
                     "          %s, %s, %s, %s, %s, %s, %s)",
                     location.dev_id, location.lat, location.lon, 
                     location.alt, location.cLat, location.cLon,
                     location.gps_time, location.name,
                     location.category, location.type,
                     location.speed, location.degree,
                     location.cellid, location.locate_error)
    if location.lat and location.lon:
        track_key = get_track_key(location.dev_id)
        track = redis.get(track_key)
        # if track is on, just put PVT into redis 
        # maybe put cellid into redis later. 
        #if track and (int(track) == 1) and (location.get("Tid", None) != EVENTER.TRIGGERID.PVT): 
        #    return lid
        #NOTE: if location's type is gps, put it into redis
        if track and (int(track) == 1) and (location.type != 0):
            return lid

        location_key = get_location_key(location.dev_id)
        last_location = redis.getvalue(location_key)
        if (last_location and (location.gps_time > last_location['timestamp'])) or\
            not last_location:

            logging.info("[PUBLIC] Keep location in redis. tid: %s, location: %s", 
                         location.dev_id, location)
            mem_location = {'id':lid,
                            'latitude':location.lat,
                            'longitude':location.lon,
                            'type':location.type,
                            'clatitude':location.cLat,
                            'clongitude':location.cLon,
                            'timestamp':location.gps_time,
                            'name':location.name,
                            'degree':location.degree,
                            'speed':location.speed,
                            'locate_error':location.locate_error}
            location_key = get_location_key(location.dev_id)
            redis.setvalue(location_key, mem_location, EVENTER.LOCATION_EXPIRY)

            if int(location.type) == 0: # gps
                logging.info("[PUBLIC] Keep gps_location in gps_redis. tid: %s, location: %s", 
                             location.dev_id, location)
                location_key = get_gps_location_key(location.dev_id)
                redis.setvalue(location_key, mem_location, EVENTER.LOCATION_EXPIRY)

    return lid

def get_alarm_mobile(tid, db, redis):
    """Get the alarm mobile associate with the terminal.
    """
    alarm_mobile = ''
    t = db.get("SELECT cid FROM V_TERMINAL WHERE tid = %s LIMIT 1", tid)
    cid = t.cid if t.get('cid', None) is not None else '0'
    corp = db.get("SELECT name, alarm_mobile FROM T_CORP WHERE cid = %s", cid)
    if corp:
        alarm_mobile = corp['alarm_mobile']
    return alarm_mobile

def get_terminal_type_by_tid(tid):
    ttype = 'unknown'
    base = [str(x) for x in range(10)] + [ chr(x) for x in range(ord('A'),ord('A')+6)]
    try:
        tid_hex2dec = str(int(tid.upper(), 16))
    except:
        logging.info("[PUBLIC] Terminal %s is illegale, can not transfer into 10 hexadecimal. It's type is unknown", tid)
        return ttype
    num = int(tid_hex2dec)
    mid = []
    while True:
        if num == 0: break
        num,rem = divmod(num, 2)
        mid.append(base[rem])
    bin_tid = ''.join([str(x) for x in mid[::-1]])
    l = 40 - len(bin_tid)
    s = '0' * l
    sn= s + bin_tid
    ttype = sn[15:18]
    if ttype == "000":
        ttype = 'zj100'   
    elif ttype == '001':
        ttype = 'zj200'
    return ttype

def get_group_info_by_tid(db, tid):
    
    group_info = {'group_id':-1, 'group_name':''}

    group = db.query("SELECT T_GROUP.id as group_id, T_GROUP.name as group_name FROM T_TERMINAL_INFO,T_GROUP"
                    " WHERE T_TERMINAL_INFO.group_id = T_GROUP.id and tid = %s", tid)
    if group:
        group_info=group[0]

    return group_info

# Feature: mannual_status 
def update_mannual_status(db, redis, tid, mannual_status):
    """Update mannual status in db and redis.

    强力设防: mannual_status 1：move_val 60  staic_val 0
    智能设防: mannual_status 2：move_val  0 stati_val 180
    撤防 mannual_status 0：move_val  0 stati_val 180

    开启停车设防: parking_defend 1  move_val  0 stati_val 180
    关闭停车设防: parking_defend 0  move_val 60  staic_val 0
    """
    # NOTE: modify the terminal_info in redis.
    terminal_info_key = get_terminal_info_key(tid)
    terminal_info = redis.getvalue(terminal_info_key)
    if terminal_info:
        terminal_info['mannual_status'] = mannual_status
        redis.setvalue(terminal_info_key, terminal_info)

    db.execute("UPDATE T_TERMINAL_INFO "
               "  SET mannual_status = %s"
               "  WHERE tid=%s",
               mannual_status, tid)
    sessionID_key = get_terminal_sessionID_key(tid)
    logging.info("[PUBLIC] Termianl %s delete session in redis.", tid)
    redis.delete(sessionID_key)
    logging.info("[PUBLIC] Terminal update mannual_status. tid: %s, mannual_status: %s",
                 tid, mannual_status)


# Feature: notify_maintainer
def notify_maintainer(db, redis, content, category):
    """Notify alarm info to maintainers.
    @param: category, 1: gateway
                      2: eventer
    """
    mobiles = []
    emails = []
    alarm_key = 'maintainer_alarm:%s' % category
    alarm_interval = 60 * 5 # 5 minutes

    alarm_flag = redis.getvalue(alarm_key)

    if not alarm_flag:
        maintainers = db.query("SELECT mid, mobile, email FROM T_MAINTAINER WHERE valid = 1")

        for item in maintainers:
            mobiles.append(item['mobile'])
            emails.append(item['email'])

        for mobile in mobiles:
            SMSHelper.send(mobile, content)

        for email in emails:
            EmailHelper.send(email, content)

        redis.setvalue(alarm_key, True, alarm_interval)

        logging.info("[PUBLIC] Notify alarm to maintainers. content: %s, category: %s.",
                     content, category)
    else:
        logging.info("[PUBLIC] Notify alarm is ignored in 5 minutes. content: %s, category: %s.",
                     content, category)
# For Weixin
def get_weixin_push_key(uid, t):
    """Get key for push interface(register or push packet)"""
    secret = '7c2d6047c7ad95f79cdb985e26a92141'
    s = uid + str(t) + secret

    m = hashlib.md5()
    m.update(s)
    key = m.hexdigest()

    return key.decode('utf8')

# for YDWQ
def update_terminal_info(db, redis, t_info):
    """Update terminal's info in db and redis.
    """
    terminal_info_key = get_terminal_info_key(t_info['tid'])
    terminal_info = QueryHelper.get_terminal_info(t_info['tid'],
                                                  db, redis)

    #1: db
    fields = []
    # gps, gsm, pbat, changed by position report
    keys = ['gps', 'gsm', 'pbat', 'login']
    for key in keys:
        value = t_info.get(key, None)
        if value is not None and value != terminal_info[key]:
            fields.append(key + " = " + str(t_info[key]))

    set_clause = ','.join(fields)
    if set_clause:
        db.execute("UPDATE T_TERMINAL_INFO"
                   "  SET " + set_clause + 
                   "  WHERE tid = %s",
                   t_info['tid'])
    #2: redis
    for key in terminal_info:
        value = t_info.get(key, None)
        if value is not None:
            terminal_info[key] = value
    redis.setvalue(terminal_info_key, terminal_info)

    return terminal_info

def update_terminal_status(redis, tid, address='DUMMY_ADDRESS'):
    terminal_status_key = get_terminal_address_key(tid)
    redis.setvalue(terminal_status_key, address, GATEWAY.YDWQ_HEARTBEAT_INTERVAL) # 30 minuts

def record_attendance(db, a_info):
    db.execute("INSERT INTO T_ATTENDANCE(mobile, comment, timestamp, lid)"
               "  VALUES(%s, %s, %s, %s)",
               a_info['mobile'], a_info['comment'], a_info['timestamp'], a_info['lid'])

