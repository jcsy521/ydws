# -*- coding: utf-8 -*-

import logging

from helpers.queryhelper import QueryHelper
from misc import *
from constants import EVENTER


def delete_terminal(tid, db, redis, del_user=True):
    terminal = db.get("SELECT mobile, owner_mobile FROM T_TERMINAL_INFO"
                      "  WHERE tid = %s", tid)
    user = db.get("SELECT id FROM T_USER"
                  "  WHERE mobile = %s",
                  terminal.owner_mobile)
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
    rids = db.query("SELECT rid FROM T_REGION_TERMINAL"
                    "  WHERE tid = %s", tid)
    tmobile = terminal.mobile if terminal else ""
    for item in [tid, tmobile]:
        sessionID_key = get_terminal_sessionID_key(item)
        address_key = get_terminal_address_key(item)
        info_key = get_terminal_info_key(item)
        lq_sms_key = get_lq_sms_key(item)
        lq_interval_key = get_lq_interval_key(item)
        location_key = get_location_key(item)
        del_data_key = get_del_data_key(item)
        keys = [sessionID_key, address_key, info_key, lq_sms_key, lq_interval_key,
                location_key, del_data_key]
        for rid in rids:
            region_status_key = get_region_status_key(item, rid)
            keys.append(region_status_key)
        redis.delete(*keys)
    # clear db
    db.execute("DELETE FROM T_TERMINAL_INFO"
               "  WHERE tid = %s", 
               tid) 
    if user:
        if del_user:
            terminals = db.query("SELECT id FROM T_TERMINAL_INFO"
                                 "  WHERE owner_mobile = %s"
                                 "    AND group_id = -1",
                                 terminal.owner_mobile)
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
        logging.info("[GW] User of %s: %s already not exist.", tid, terminal.owner_mobile)
    logging.info("[GW] Delete Terminal: %s, tmobile: %s, umobile: %s",
                 tid, tmobile, (terminal.owner_mobile if user else None))

def insert_location(location, db, redis):
    # insert data into T_LOCATION
    lid = db.execute("INSERT INTO T_LOCATION"
                     "  VALUES (NULL, %s, %s, %s, %s, %s, %s, %s,"
                     "          %s, %s, %s, %s, %s, %s)",
                     location.dev_id, location.lat, location.lon, 
                     location.alt, location.cLat, location.cLon,
                     location.gps_time, location.name,
                     location.category, location.type,
                     location.speed, location.degree,
                     location.cellid)
    if location.cLat and location.cLon:
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
