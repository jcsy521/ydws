# -*- coding: utf-8 -*-

import logging
import time 

from helpers.queryhelper import QueryHelper
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
    logging.info("Record the add action, tmobile: %s, group_id: %s, add_time: %s",
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
    logging.info("Record the del action, tmobile: %s, group_id: %s, del_time: %s",
                 tmobile, group_id, del_time)
    db.execute("INSERT INTO T_BIND_LOG(tmobile, group_id, op_type, del_time)" 
               " VALUES(%s, %s, %s, %s)", 
               tmobile, group_id, UWEB.OP_TYPE.DEL, del_time)              

def clear_data(tid, db):
    """Just clear the info associated with terminal in database.
    """
    db.execute("DELETE FROM T_LOCATION"
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
    logging.info("Clear db data of terminal: %s", tid)

def delete_terminal(tid, db, redis, del_user=True):
    """Delete terminal from platform and clear the associated info.
    """
    terminal = db.get("SELECT mobile, owner_mobile, group_id FROM T_TERMINAL_INFO"
                      "  WHERE tid = %s", tid)
    #if not terminal:
    #    logging.info("Terminal: %s already not existed.", tid)
    #    return
        
    user = None
    if terminal:
        user = db.get("SELECT id FROM T_USER"
                      "  WHERE mobile = %s",
                      terminal.owner_mobile)
    rids = db.query("SELECT rid FROM T_REGION_TERMINAL"
                    "  WHERE tid = %s", tid)
    # clear history data
    key = get_del_data_key(tid)
    flag = redis.get(key)
    if flag and int(flag) == 1:
        db.execute("DELETE FROM T_LOCATION"
                   "  WHERE tid = %s",
                   tid)
        db.execute("DELETE FROM T_EVENT"
                   " WHERE tid = %s",
                   tid)
        db.execute("DELETE FROM T_CHARGE"
                   " WHERE tid = %s",
                   tid)
        logging.info("Delete db data of terminal: %s", tid)

    # clear redis
    tmobile = terminal.mobile if terminal else ""
    for item in [tid, tmobile]:
        sessionID_key = get_terminal_sessionID_key(item)
        address_key = get_terminal_address_key(item)
        info_key = get_terminal_info_key(item)
        lq_sms_key = get_lq_sms_key(item)
        lq_interval_key = get_lq_interval_key(item)
        location_key = get_location_key(item)
        del_data_key = get_del_data_key(item)
        track_key = get_track_key(item)
        login_time_key = get_login_time_key(item)
        offline_lq_key = get_offline_lq_key(item)
        lqgz_interval_key = get_lqgz_interval_key(item)
        lqgz_key = get_lqgz_key(item)
        alarm_info_key = get_alarm_info_key(item)
        keys = [sessionID_key, address_key, info_key, lq_sms_key, lq_interval_key,
                location_key, del_data_key, track_key, login_time_key,
                offline_lq_key, lqgz_interval_key, lqgz_key, alarm_info_key]
        for rid in rids:
            region_status_key = get_region_status_key(item, rid)
            keys.append(region_status_key)
        redis.delete(*keys)

    # clear db
    db.execute("DELETE FROM T_REGION_TERMINAL"
               "  WHERE tid = %s",
               tid)
    if terminal:
        # record the del action.
        record_del_action(terminal.mobile, terminal.group_id, int(time.time()), db)

    db.execute("DELETE FROM T_TERMINAL_INFO"
               "  WHERE tid = %s", 
               tid) 
    if user:
        if del_user:
            terminals = db.query("SELECT id FROM T_TERMINAL_INFO"
                                 "  WHERE owner_mobile = %s"
                                 #"    AND group_id = -1",
                                 "    AND service_status = %s",
                                 terminal.owner_mobile,
                                 UWEB.SERVICE_STATUS.ON)
            # clear user
            if len(terminals) == 0:
                db.execute("DELETE FROM T_USER"
                           "  WHERE mobile = %s",
                           terminal.owner_mobile)

                lastinfo_key = get_lastinfo_key(terminal.owner_mobile)
                lastinfo_time_key = get_lastinfo_time_key(terminal.owner_mobile)
                ios_id_key = get_ios_id_key(terminal.owner_mobile)
                ios_badge_key = get_ios_badge_key(terminal.owner_mobile)
                keys = [lastinfo_key, lastinfo_time_key, ios_id_key, ios_badge_key]
                redis.delete(*keys)
                logging.info("[GW] Delete User: %s", terminal.owner_mobile)
    else:
        logging.info("[GW] User of %s already not exist.", tid)

    logging.info("[GW] Delete Terminal: %s, tmobile: %s, umobile: %s",
                 tid, tmobile, (terminal.owner_mobile if terminal else None))

def insert_location(location, db, redis):
    """Insert whole-data into T_LOCATION.
    """
    location = DotDict(location)
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

    return lid

def get_terminal_type_by_tid(tid):
    ttype = 'unknown'
    base = [str(x) for x in range(10)] + [ chr(x) for x in range(ord('A'),ord('A')+6)]
    try:
        tid_hex2dec = str(int(tid.upper(), 16))
    except:
        logging.info("[GW] Terminal %s is illegale, can not transfer into 10 hexadecimal. It's type is unknown", tid)
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

