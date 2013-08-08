# -*- coding: utf-8 -*-

import logging
import time 

from helpers.queryhelper import QueryHelper
from misc import *
from utils.dotdict import DotDict
from constants import EVENTER, UWEB

def record_terminal_subscription(db, tmobile, group_id, begintime, add_time, op_type):

    db.execute("INSERT INTO T_SUBSCRIPTION_LOG(tmobile, group_id, begintime, add_time, op_type)" 
               "   VALUES(%s, %s, %s, %s, %s)" 
               " ON DUPLICATE KEY" 
               " UPDATE add_time=values(add_time)," 
               " group_id=values(group_id)," 
               " op_type=values(op_type)", 
               tmobile, group_id, begintime, add_time, op_type)

def clear_data(tid, db):
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
    terminal = db.get("SELECT mobile, owner_mobile FROM T_TERMINAL_INFO"
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
        db.execute("DELETE FROM T_REGION_TERMINAL"
                   "  WHERE tid = %s",
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
    if terminal:
        db.execute("UPDATE T_SUBSCRIPTION_LOG SET del_time = %s, op_type=%s"
                   "  WHERE tmobile = %s ", 
                   int(time.time()), UWEB.OP_TYPE.DEL, terminal.mobile)

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
    # insert data into T_LOCATION
    location = DotDict(location)
    lid = db.execute("INSERT INTO T_LOCATION"
                     "  VALUES (NULL, %s, %s, %s, %s, %s, %s, %s,"
                     "          %s, %s, %s, %s, %s, %s)",
                     location.dev_id, location.lat, location.lon, 
                     location.alt, location.cLat, location.cLon,
                     location.gps_time, location.name,
                     location.category, location.type,
                     location.speed, location.degree,
                     location.cellid)
    if location.lat and location.lon:
        track_key = get_track_key(location.dev_id)
        track = redis.get(track_key)
        # if track is on, just put PVT into redis 
        # maybe put cellid into redis later. 
        if track and (int(track) == 1) and (location.get("Tid", None) != EVENTER.TRIGGERID.PVT): 
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
                            'speed':location.speed}
            location_key = get_location_key(location.dev_id)
            redis.setvalue(location_key, mem_location, EVENTER.LOCATION_EXPIRY)

    return lid
