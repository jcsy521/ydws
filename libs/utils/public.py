# -*- coding: utf-8 -*-

import logging
import time 

from helpers.queryhelper import QueryHelper
from helpers.smshelper import SMSHelper
from helpers.emailhelper import EmailHelper
from helpers.wspushhelper import WSPushHelper
from helpers.lbmpsenderhelper import LbmpSenderHelper
from tornado.escape import json_decode, json_encode

from misc import *
from utils.dotdict import DotDict
from constants import EVENTER, UWEB, GATEWAY

##NOTE:Part  Record 

# Feature: bind_log 
def record_add_action(bind_info, db):
    """Record the add action of one mobile.
    @params: bind_info, {'tid':'',
                         'tmobile':'', 
                         'umobile':'', 
                         'group_id','',
                         'cid','',
                         'add_time':'',}
    @param: db
    """
    logging.info("[PUBLIC] Record the add action, bind_info:%s",
                 bind_info)
    db.execute("INSERT INTO T_BIND_LOG(tid, tmobile, umobile, group_id, cid, op_type, add_time)" 
               " VALUES(%s, %s, %s, %s, %s, %s, %s)", 
               bind_info.get('tid',''), 
               bind_info.get('tmobile',''), 
               bind_info.get('umobile',''), 
               bind_info.get('group_id',-1), 
               bind_info.get('cid',''), 
               UWEB.OP_TYPE.ADD, 
               bind_info.get('add_time',0))
               
def record_del_action(bind_info, db):
    """Record the del action of one mobile.
    @params: bind_info, {'tid':'',
                         'tmobile':'', 
                         'umobile':'', 
                         'group_id','',
                         'cid','',
                         'del_time':'',}
    @param: db
    """
    logging.info("[PUBLIC] Record the del action, bind_info: %s",
                 bind_info)
    db.execute("INSERT INTO T_BIND_LOG(tid, tmobile, umobile, group_id, cid, op_type, del_time)" 
               " VALUES(%s, %s, %s, %s, %s, %s, %s)", 
               bind_info.get('tid',''), 
               bind_info.get('tmobile',''), 
               bind_info.get('umobile',''), 
               bind_info.get('group_id',-1), 
               bind_info.get('cid',''), 
               UWEB.OP_TYPE.DEL, 
               bind_info.get('del_time',0))

def record_manual_status(db, redis, tid, mannual_status):
    """Record the mannual_status of one terminal.

    @params: db
    @params: redis 
    @params: tid 
    @params: mannual_status 
    """

    terminal = QueryHelper.get_terminal_basic_info(tid, db)
    db.execute("INSERT INTO T_MANUAL_LOG(tid, tmobile, umobile,"
               "    group_id, cid, manual_status, timestamp)" 
               "  VALUES(%s, %s, %s, %s, %s, %s, %s)", 
               terminal.get('tid',''), 
               terminal.get('tmobile',''), 
               terminal.get('umobile',''), 
               terminal.get('group_id',-1), 
               terminal.get('cid',''), 
               mannual_status,
               int(time.time()))

    logging.info("[PUBLIC] Record the mannual status, tid: %s, mannual_status: %s",
                 tid, mannual_status)


def record_alarm_info(db, redis, alarm):
    """Record the alarm info in the redis.
    @param: db
    @param: redis 
    @param: alarm 

    tid --> alarm_info:[
                         {
                           keeptime // keep alarm's keeptime when kept in reids, not timestamp alarm occurs
                           type, 
                           category,
                           latitude,
                           longitude, 
                           clatitude,
                           clongitude,
                           timestamp,
                           name,
                           degree, 
                           speed,
                           # for regions
                           region_id,
                         },
                         ...
                       ]
    alarm_info is a list with one or many alarms.
    """
    alarm_info_key = get_alarm_info_key(alarm['tid'])
    alarm_info = redis.getvalue(alarm_info_key)
    alarm_info = alarm_info if alarm_info else []
    alarm['keeptime'] = int(time.time())
    alarm_info.append(alarm)

    #NOTE: only store the alarm during past 10 minutes.
    alarm_info_new = []
    for alarm in alarm_info:
        if alarm.get('keeptime', None) is None:
            alarm['keeptime'] = alarm['timestamp']

        if alarm['keeptime'] + 60*10 < int(time.time()):
            pass
        else:
            alarm_info_new.append(alarm)

    redis.setvalue(alarm_info_key, alarm_info_new, EVENTER.ALARM_EXPIRY)

##NOTE: Part: Modify 

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
        db.execute("DELETE FROM T_TERMINAL_INFO"
                   "  WHERE tid = %s", 
                   tid) 

        db.execute("DELETE FROM T_EVENT"
                   " WHERE tid = %s",
                   tid)

        db.execute("DELETE FROM T_CHARGE"
                   " WHERE tid = %s",
                   tid)

        db.execute("DELETE FROM T_REGION_TERMINAL"
                   "  WHERE tid = %s",
                   tid)

        db.execute("DELETE FROM T_REGION_TERMINAL"
                   "  WHERE tid = %s", tid)

        db.execute("DELETE FROM T_DAY_NOTIFICATION"
                   "  WHERE tid = %s", tid)

        db.execute("DELETE FROM T_MILEAGE_NOTIFICATION"
                   "  WHERE tid = %s", tid)

        #NOTE: check whether clear history data
        key = get_del_data_key(tid)
        flag = redis.get(key)
        if flag and int(flag) == 1: # clear history data
            redis.delete(key)
            db.execute("DELETE FROM T_LOCATION"
                       "  WHERE tid = %s",
                       tid)

            db.execute("DELETE FROM T_MILEAGE_LOG"
                       "  WHERE tid = %s",
                       tid)

            db.execute("DELETE FROM T_STOP"
                       "  WHERE tid = %s",
                       tid)

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
    Ole version. Now, it does nothing.
    """
    pass

def delete_terminal_new(tid, db, redis, del_user=True):
    """Delete terminal from platform and clear the associated info.
    """
    terminal = db.get("SELECT mobile, owner_mobile, group_id FROM T_TERMINAL_INFO"
                      "  WHERE tid = %s", tid)
    if not terminal:
        logging.info("Terminal: %s already does not exist, do nothing.", tid)
        return
    else:
        t_info = QueryHelper.get_terminal_basic_info(tid, db)         
        #NOTE: record the del action.
        corp = QueryHelper.get_corp_by_gid(terminal.group_id, db) 
        bind_info = dict(tid=tid,
                         tmobile=terminal.mobile,
                         umobile=terminal.owner_mobile,
                         group_id=terminal.group_id,
                         cid=corp.get('cid', '') if corp else '',
                         del_time=int(time.time()))
        record_del_action(bind_info, db)
        WSPushHelper.pushS3(tid, db, redis, t_info)
        clear_data(tid, db, redis)
        logging.info("[PUBLIC] Delete Terminal: %s, tmobile: %s, umobile: %s",
                     tid, terminal.mobile, terminal.owner_mobile)

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
    old_user = db.get("SELECT id FROM T_USER WHERE mobile = %s", user['umobile'])
    if not old_user:
        db.execute("INSERT INTO T_USER(uid, password, name, mobile, address, email)"
                   "  VALUES(%s, password(%s), %s, %s, %s, %s)",
                   user['umobile'], user['password'],
                   user.get('uname',''), user['umobile'],
                   user.get('address',''), user.get('email',''))

    # add sms_option
    sms_option = db.get("SELECT id FROM T_SMS_OPTION WHERE uid= %s", user['umobile'])
    if sms_option:
        pass
    else:
        db.execute("INSERT INTO T_SMS_OPTION(uid)"
                   "  VALUES(%s)",
                   user['umobile'])

    logging.info("[PUBLIC] Add user, umobile: %s, user: %s.",
                 user['umobile'], user)

def add_terminal(terminal, db, redis):
    """"Add a terminal.
    @param: terminal, {'tid':'',
                       'tmobile':'', 
                       'owner_mobile':'',
                       'group_id':'',
                       'dev_type':'',
                       'imsi':'',
                       'imei':'',
                       'factory_name':'',
                       'softversion':'',
                       'keys_num':'',
                       'bt_name':'',
                       'bt_mac':'',
                       'login':'',
                       'mannual_status':'',
                       'alias':'',
                       'icon_type':'',
                       'login_permit':'',
                       'push_status':'',
                       'vibl':'',
                       'use_scene':'',
                       'biz_type':'',
                       'activation_code':'',
                       'service_status':'',
                       'begintime':'',
                       'endtime':'',
                       'offline_time':''
                       'speed_limit':''
                       'stop_interval':''
                       'distance_current':''
                       # car
                       'cnum':'',
                       }
    @param: db
    @param: redis
    """
    if terminal.get('tid',''): 
        tid = terminal['tid']
    else:
        tid = terminal['tmobile']

    # add terminal 28 items.
    db.execute("INSERT INTO T_TERMINAL_INFO(tid, mobile, owner_mobile,"
               "  group_id, dev_type, imsi, imei, factory_name, softversion,"
               "  keys_num, bt_name, bt_mac, login, mannual_status, alias,"
               "  icon_type, login_permit, push_status, vibl, use_scene,"
               "  biz_type, activation_code, service_status, begintime,"
               "  endtime, offline_time, speed_limit, stop_interval,"
               "  distance_current)"
               "  VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,"
               "          %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,"
               "          %s, %s, %s, %s, %s)",
               tid, terminal.get('tmobile'), terminal.get('owner_mobile'),
               terminal.get('group_id', -1), terminal.get('dev_type', 'A'),
               terminal.get('imsi', ''), terminal.get('imei', ''),
               terminal.get('factory_name', ''), terminal.get('softversion', ''),
               terminal.get('keys_num', 0), terminal.get('bt_name', ''),
               terminal.get('bt_mac', ''), terminal.get('login', 0),
               terminal.get('mannual_status', 1), terminal.get('alias', ''),
               terminal.get('icon_type', 0), terminal.get('login_permit', 1),
               terminal.get('push_status', 1), terminal.get('vibl', 1),
               terminal.get('use_scene', 3), terminal.get('biz_type', 0),
               terminal.get('activation_code', ''), terminal.get('service_status', 1), 
               terminal.get('begintime'), terminal.get('endtime'),
               terminal.get('offline_time'), terminal.get('speed_limit', 120),
               terminal.get('stop_interval',0), terminal.get('distance_current',0))
    
    #add car tnum --> cnum
    car = db.get("SELECT id FROM T_CAR WHERE tid= %s", tid)
    if car:
        db.execute("DELETE FROM T_CAR WHERE tid = %s", tid)
    
    db.execute("INSERT INTO T_CAR(tid, cnum, type, color, brand)"
               "  VALUES(%s, %s, %s, %s, %s)",
               tid, terminal.get('cnum',''), 
               terminal.get('ctype', 1), terminal.get('ccolor', 0), 
               terminal.get('cbrand',''))
    # wspush to client
    WSPushHelper.pushS3(tid, db, redis)
    logging.info("[PUBLIC] Add terminal, tid: %s, terminal: %s.",
                 tid, terminal)
 
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
    if t:
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
                     "  WHERE T_TERMINAL_INFO.group_id = T_GROUP.id and tid = %s", tid)
    if group:
        group_info=group[0]

    return group_info

# Feature: mannual_status 
def update_mannual_status(db, redis, tid, mannual_status):
    """Update mannual status in db and redis.

    强力设防: mannual_status 1：move_val 60  staic_val 0
    智能设防: mannual_status 2：move_val  0 stati_val 180
    撤防 mannual_status 0：move_val  0 stati_val 180

    开启停车设防: parking_defend 1: mannual_status 2, move_val  0 stati_val 180
    关闭停车设防: parking_defend 0: mannual_status 1, move_val 60  staic_val 0
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

    record_manual_status(db, redis, tid, mannual_status)

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

def update_terminal_info(db, redis, t_info):
    """Update terminal's info in db and redis.
    NOTE: 
    Only those properties which are different from platform is needed to change.
    """
    tid = t_info['dev_id']
    terminal_info_key = get_terminal_info_key(tid)
    terminal_info = QueryHelper.get_terminal_info(tid,
                                                  db, redis)

    #1: db
    fields = []
    # gps, gsm, pbat, changed by position report
    keys = ['mobile', 'defend_status', 'login', 'keys_num', 'fob_status', 'mannual_status', 
            'softversion', 'bt_mac', 'bt_name', 'dev_type']
    for key in keys:
        value = t_info.get(key, None)
        t_value = terminal_info.get(key, '')
        if value is not None and value != t_value:
            fields.append(key + " = " + "'" + str(t_info[key]) + "'")
    if 'login_time' in t_info:
        fields.append('login_time' + " = " + str(t_info['login_time']))
        login_time_key = get_login_time_key(tid)
        redis.setvalue(login_time_key, t_info['login_time'])
    set_clause = ','.join(fields)
    if set_clause:
        sql_cmd = ("UPDATE T_TERMINAL_INFO "
                   "  SET " + set_clause + 
                   "  WHERE tid = %s")
        db.execute(sql_cmd, tid)
    #2: redis
    for key in terminal_info:
        value = t_info.get(key, None)
        if value is not None:
            terminal_info[key] = value
    redis.setvalue(terminal_info_key, terminal_info)

    #terminal basic info
    WSPushHelper.pushS6(tid, db, redis)
    return terminal_info 

def update_terminal_dynamic_info(db, redis, location):
    """Update terminal's dynamic info in db and redis.
    Then inclues gps, gsm, pbat.
    """
    # db
    tid = location.dev_id
    fields = []

    #NOTE: only gps, gsm, pbat should be updated
    keys = ['gps', 'gsm', 'pbat']
    for key in keys:
        if location.get(key, None) is not None:
            fields.append(key + " = " + str(location[key]))
    set_clause = ','.join(fields)
    if set_clause:
        db.execute("UPDATE T_TERMINAL_INFO"
                   "  SET " + set_clause +
                   "  WHERE tid = %s",
                   tid)
    # redis
    terminal_info = QueryHelper.get_terminal_info(tid, db, redis)
    if terminal_info:
        terminal_info_key = get_terminal_info_key(tid)
        for key in terminal_info:
            value = location.get(key, None)
            if value is not None:
                terminal_info[key] = value
        redis.setvalue(terminal_info_key, terminal_info)


def update_fob_info(db, redis, fobinfo):
    """Update fob's information.
    """
    terminal_info_key = get_terminal_info_key(fobinfo['dev_id'])
    terminal_info = QueryHelper.get_terminal_info(fobinfo['dev_id'],
                                                  db, redis)

    if int(fobinfo['operate']) == GATEWAY.FOB_OPERATE.ADD:
        db.execute("INSERT INTO T_FOB(tid, fobid)"
                   "  VALUES(%s, %s)"
                   "  ON DUPLICATE KEY"
                   "  UPDATE tid = VALUES(tid),"
                   "         fobid = VALUES(fobid)",
                   fobinfo['dev_id'], fobinfo['fobid'])
        fob_list = terminal_info['fob_list']
        if fob_list:
            fob_list.append(fobinfo['fobid'])
        else:
            fob_list = [fobinfo['fobid'],]
        terminal_info['fob_list'] = list(set(fob_list))
        terminal_info['keys_num'] = len(terminal_info['fob_list']) 
        db.execute("UPDATE T_TERMINAL_INFO"
                   "  SET keys_num = %s"
                   "  WHERE tid = %s", 
                   terminal_info['keys_num'], fobinfo['dev_id'])
        redis.setvalue(terminal_info_key, terminal_info)
    elif int(fobinfo['operate']) == GATEWAY.FOB_OPERATE.REMOVE:
        db.execute("DELETE FROM T_FOB"
                   "  WHERE fobid = %s"
                   "    AND tid = %s",
                   fobinfo['fobid'], fobinfo['dev_id'])
        fob_list = terminal_info['fob_list']
        if fob_list:
            if fobinfo['fobid'] in fob_list:
                fob_list.remove(fobinfo['fobid'])
        else:
            fob_list = []
        terminal_info['fob_list'] = list(set(fob_list))
        terminal_info['keys_num'] = len(terminal_info['fob_list']) 
        db.execute("UPDATE T_TERMINAL_INFO"
                   "  SET keys_num = %s"
                   "  WHERE tid = %s", 
                   terminal_info['keys_num'], fobinfo['dev_id'])
        redis.setvalue(terminal_info_key, terminal_info)
    else:
        pass


# For Weixin
def get_weixin_push_key(uid, t):
    """Get key for push interface(register or push packet)"""
    secret = '7c2d6047c7ad95f79cdb985e26a92141'
    s = uid + str(t) + secret

    m = hashlib.md5()
    m.update(s)
    key = m.hexdigest()

    return key.decode('utf8')

def subscription_lbmp(mobile):
    """ Subscription LE for new sim
    """
    data = DotDict(sim=mobile,
                   action="A")
    response = LbmpSenderHelper.forward(LbmpSenderHelper.URLS.SUBSCRIPTION, data) 
    response = json_decode(response) 
    if response['success'] == '000': 
        logging.info("[GW] mobile: %s subscription LE success! ",
                     mobile)
    else:
        logging.info("[GW] mobile: %s subscription LE failed! response:%s",
                     mobile, response)

# for YDWQ
def update_terminal_info_ydwq(db, redis, t_info):
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

