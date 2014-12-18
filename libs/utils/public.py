# -*- coding: utf-8 -*-

import logging
import time

from helpers.queryhelper import QueryHelper
from helpers.smshelper import SMSHelper
from helpers.emailhelper import EmailHelper
from helpers.wspushhelper import WSPushHelper
from helpers.lbmpsenderhelper import LbmpSenderHelper
from helpers.smshelper import SMSHelper
from tornado.escape import json_decode, json_encode

from codes.smscode import SMSCode

from misc import *
from utils.dotdict import DotDict
from constants import EVENTER, UWEB, GATEWAY, SMS

"""Part: Record log.
"""


def record_add_action(bind_info, db):
    """Record the add action of one mobile.
    :arg bind_info：dict, e.g.

        {
          'tid':'',
          'tmobile':'', 
          'umobile':'', 
          'group_id','',
          'cid','',
          'add_time':'',
        }

    :arg db: database instance.

    """
    logging.info("[PUBLIC] Record the add action, bind_info:%s",
                 bind_info)
    db.execute("INSERT INTO T_BIND_LOG(tid, tmobile, umobile, group_id, cid, op_type, add_time)"
               " VALUES(%s, %s, %s, %s, %s, %s, %s)",
               bind_info.get('tid', ''),
               bind_info.get('tmobile', ''),
               bind_info.get('umobile', ''),
               bind_info.get('group_id', -1),
               bind_info.get('cid', ''),
               UWEB.OP_TYPE.ADD,
               bind_info.get('add_time', 0))


def record_del_action(bind_info, db):
    """Record the del action of one mobile.

    @arg bind_info: dict . e.g.

        {'tid':'',
         'tmobile':'', 
         'umobile':'', 
         'group_id','',
         'cid','',
         'del_time':'',
        }

    @arg db: database instance.

    """
    logging.info("[PUBLIC] Record the del action, bind_info: %s",
                 bind_info)
    db.execute("INSERT INTO T_BIND_LOG(tid, tmobile, umobile, group_id, cid, op_type, del_time)"
               " VALUES(%s, %s, %s, %s, %s, %s, %s)",
               bind_info.get('tid', ''),
               bind_info.get('tmobile', ''),
               bind_info.get('umobile', ''),
               bind_info.get('group_id', -1),
               bind_info.get('cid', ''),
               UWEB.OP_TYPE.DEL,
               bind_info.get('del_time', 0))


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
               terminal.get('tid', ''),
               terminal.get('tmobile', ''),
               terminal.get('umobile', ''),
               terminal.get('group_id', -1),
               terminal.get('cid', ''),
               mannual_status,
               int(time.time()))

    logging.info("[PUBLIC] Record the mannual status, tid: %s, mannual_status: %s",
                 tid, mannual_status)


def record_alarm_info(db, redis, alarm):
    """Record the alarm info in the redis.

    :arg db： database instance
    :arg redis：redis instance
    :arg alarm: dict,  

    Alarm_info is a list with one or many alarms.

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

    """
    alarm_info_key = get_alarm_info_key(alarm['tid'])
    alarm_info = redis.getvalue(alarm_info_key)
    alarm_info = alarm_info if alarm_info else []
    alarm['keeptime'] = int(time.time())
    alarm_info.append(alarm)

    # NOTE: only store the alarm during past 10 minutes.
    alarm_info_new = []
    for alarm in alarm_info:
        if alarm.get('keeptime', None) is None:
            alarm['keeptime'] = alarm['timestamp']

        if alarm['keeptime'] + 60 * 10 < int(time.time()):
            pass
        else:
            alarm_info_new.append(alarm)

    redis.setvalue(alarm_info_key, alarm_info_new, EVENTER.ALARM_EXPIRY)
    logging.info("[PUBLIC] Record the alarm status, tid: %s", alarm['tid'])


def record_login_user(login_info, db):
    """Record the log-in info of users.

    :arg login_info, e.g.

        {
          'uid':'',
          'role':'',  int. e.g. 0: person; 1: operator; 2: enterprise
          'method':'', int. e.g.  0: web; 1: android; 2: ios
          'versionname':''
        }

    :arg db: database instance.

    """
    db.execute("INSERT INTO T_LOGIN_LOG(uid, role, method, timestamp)"
               "  values(%s, %s, %s, %s)",
               login_info['uid'], login_info['role'], login_info['method'], int(time.time()))

    versionname = login_info.get('versionname', '')
    if versionname:
        if method == 1:  # android
            db.execute("UPDATE T_USER SET android_versionname = %s "
                       "  WHERE uid = %s", versionname, login_info['uid'])
        elif method == 2:  # ios
            self.db.execute("UPDATE T_USER SET ios_versionname = %s "
                            "  WHERE uid = %s", versionname, login_info['uid'])
        else:
            logging.info(
                "[PUBLIC] method: %s is invalid.", login_info['method'])
    else:
        logging.info("[PUBLIC] versionname is empty: %s", versionname)
    logging.info("[PUBLIC] Record the login user, uid: %s", login_info['uid'])


def record_share(db, share):
    """Record the information-share log of one user.

    :arg db: database instance
    :arg share：dict, e.g.

    """
    db.execute("INSERT INTO T_SHARE_LOG(umobile, platform, timestamp, tmobile, tid)"
               "  VALUES(%s, %s, %s, %s, %s)",
               share['umobile'], share['platform'], int(time.time()),
               share['tmobile'], share['tid'])


def record_announcement(db, announcement):
    """Record the announcement log of one corp.

    :arg db: database instance
    :arg announcement: dict, e.g.

        {
          'cid':'',
          'content':'',
          'mobiles':''
        }

    """
    db.execute("INSERT INTO T_ANNOUNCEMENT_LOG(umobile, content, timestamp, mobiles)"
               "  VALUES(%s, %s, %s, %s)",
               announcement['cid'], announcement['content'], int(time.time()),
               announcement['mobiles'])


def record_script_download(db, script):
    """Record the script log of one corp.

    :arg db: database instance
    :arg script: dict, e.g.

        {
          'tid':'',
          'versionname':'',
        }

    """
    db.execute("INSERT INTO T_SCRIPT_DOWNLOAD(tid, versionname, timestamp)"
               " VALUES(%s, %s, %s)",
               script['tid'],
               script['versionname'], int(time.time()))


"""Part: Terminal modifying.
"""


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

        # NOTE: check whether clear history data
        key = get_del_data_key(tid)
        flag = redis.get(key)
        if flag and int(flag) == 1:  # clear history data
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
            tid_keys = redis.keys('*:%s' % tid)
            keys.extend(tid_keys)

        if tmobile:
            tmobile_keys = redis.keys('*:%s' % tmobile)
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
        # NOTE: record the del action.
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
    if terminal.get('tid', ''):
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
               terminal.get('factory_name', ''), terminal.get(
                   'softversion', ''),
               terminal.get('keys_num', 0), terminal.get('bt_name', ''),
               terminal.get('bt_mac', ''), terminal.get('login', 0),
               terminal.get('mannual_status', 1), terminal.get('alias', ''),
               terminal.get('icon_type', 0), terminal.get('login_permit', 1),
               terminal.get('push_status', 1), terminal.get('vibl', 1),
               terminal.get('use_scene', 3), terminal.get('biz_type', 0),
               terminal.get('activation_code', ''), terminal.get(
                   'service_status', 1),
               terminal.get('begintime'), terminal.get('endtime'),
               terminal.get('offline_time'), terminal.get('speed_limit', 120),
               terminal.get('stop_interval', 0), terminal.get('distance_current', 0))

    # add car tnum --> cnum
    car = db.get("SELECT id FROM T_CAR WHERE tid= %s", tid)
    if car:
        db.execute("DELETE FROM T_CAR WHERE tid = %s", tid)

    db.execute("INSERT INTO T_CAR(tid, cnum, type, color, brand)"
               "  VALUES(%s, %s, %s, %s, %s)",
               tid, terminal.get('cnum', ''),
               terminal.get('ctype', 1), terminal.get('ccolor', 0),
               terminal.get('cbrand', ''))
    # NOTE: wspush to client
    WSPushHelper.pushS3(tid, db, redis)
    logging.info("[PUBLIC] Add terminal, tid: %s, terminal: %s.",
                 tid, terminal)


def update_terminal_info(db, redis, t_info):
    """Update terminal's info in db and redis.

    :arg db: database instance 
    :arg redis: redis instance
    :arg terminal: dict, e.g.

        {
          'mobile':'',
          ...
        }

    NOTE: 
    Only those properties which are different from platform is needed to change.
    """
    tid = t_info['dev_id']
    terminal_info_key = get_terminal_info_key(tid)
    terminal_info = QueryHelper.get_terminal_info(tid,
                                                  db, redis)

    # 1: db
    set_clause_dct = []
    # gps, gsm, pbat, changed by position report
    keys = ['mobile', 'defend_status', 'login', 'keys_num', 'fob_status', 'mannual_status',
            'softversion', 'bt_mac', 'bt_name', 'dev_type']

    for key in keys:
        value = t_info.get(key, None)
        t_value = terminal_info.get(key, '')
        if value is not None and value != t_value:
            set_clause_dct.append(key + " = " + "'" + str(t_info[key]) + "'")

    if 'login_time' in t_info:
        set_clause_dct.append('login_time' + " = " + str(t_info['login_time']))
        login_time_key = get_login_time_key(tid)
        redis.setvalue(login_time_key, t_info['login_time'])

    set_clause = ','.join(set_clause_dct)
    if set_clause:
        sql_cmd = ("UPDATE T_TERMINAL_INFO "
                   "  SET " + set_clause +
                   "  WHERE tid = %s")
        db.execute(sql_cmd, tid)

    # 2: redis
    for key in terminal_info:
        value = t_info.get(key, None)
        if value is not None:
            terminal_info[key] = value
    redis.setvalue(terminal_info_key, terminal_info)

    # NOTE：wspush to client. terminal basic info
    WSPushHelper.pushS6(tid, db, redis)
    return terminal_info


def update_terminal_dynamic_info(db, redis, location):
    """Update terminal's dynamic info in db and redis.
    Then inclues gps, gsm, pbat.
    """
    # db
    tid = location.dev_id
    fields = []

    # NOTE: only gps, gsm, pbat should be updated
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

    NOTE: deprecated.
    Tracker has not fob now.
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
            fob_list = [fobinfo['fobid'], ]
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

"""Part: User modifying.
"""


def add_user(user, db, redis):
    """"Add a user.

    @arg user：dict, e.g.

        {
          'umobie':'', 
          'password':'',
          'uname':'',
          'address':'',
          'email':''
        }

    @arg db: database instance
    @arg redis: redis instance

    """
    # add user
    old_user = db.get(
        "SELECT id FROM T_USER WHERE mobile = %s", user['umobile'])
    if not old_user:
        db.execute("INSERT INTO T_USER(uid, password, name, mobile, address, email)"
                   "  VALUES(%s, password(%s), %s, %s, %s, %s)",
                   user['umobile'], user['password'],
                   user.get('uname', ''), user['umobile'],
                   user.get('address', ''), user.get('email', ''))

    # add sms_option
    sms_option = db.get(
        "SELECT id FROM T_SMS_OPTION WHERE uid= %s", user['umobile'])
    if sms_option:
        pass
    else:
        db.execute("INSERT INTO T_SMS_OPTION(uid)"
                   "  VALUES(%s)",
                   user['umobile'])

    logging.info("[PUBLIC] Add user, umobile: %s, user: %s.",
                 user['umobile'], user)


def update_password(psd_info, db, redis):
    """"Update password.

    :arg psd_info：dict, e.g.

        {
          'user_id': string, 
          'user_type': int, e.g. 1:  2： 
          'password': string,        
        }

    :arg db: database instance
    :arg redis: redis instance

    """
    user_type = str(psd_info['user_type'])
    password = psd_info['password']
    user_id = psd_info['user_id']
    if user_type == UWEB.USER_TYPE.CORP:
        db.execute("UPDATE T_CORP"
                   "  SET password = password(%s)"
                   "  WHERE cid = %s",
                   password, user_id)
    elif user_type == UWEB.USER_TYPE.OPERATOR:
        db.execute("UPDATE T_OPERATOR"
                   "  SET password = password(%s)"
                   "  WHERE oid = %s",
                   password, user_id)
    else:
        db.execute("UPDATE T_USER "
                   "  SET password = password(%s)"
                   "  WHERE uid = %s",
                   password, user_id)

        # NOTE: clear ios push list
        ios_push_list_key = get_ios_push_list_key(user_id)
        ios_push_list = redis.getvalue(ios_push_list_key)
        ios_push_list = ios_push_list if ios_push_list else []
        for iosid in ios_push_list:
            ios_badge_key = get_ios_badge_key(iosid)
            redis.delete(ios_badge_key)
            ios_push_list.remove(iosid)
        redis.set(ios_push_list_key, [])
        logging.info("[UWEB] uid:%s clear ios_push_list.", user_id)

"""Part: Region.
"""


def add_region(region, db, redis):
    """"Add a region.

    :arg region: dict, e.g.

        {
          'region_name':'', 
          'longitude':'',
          'latitude':'',
          'radius':'',
          'points':'',
          'shape':'',
          'uid':'',
          'cid':'',
          'tid':'',
        }

    :arg db: database instance
    :arg redis: redis instance

    :arg rid: int 

    """
    uid = region.get('uid', None)
    if uid:  # create region for user and bind it to terminal.
        rid = db.execute("INSERT T_REGION(name, longitude, latitude,"
                         "  radius, points, shape, uid)"
                         "  VALUES(%s, %s, %s, %s, %s, %s, %s)",
                         region.get('region_name', ''),
                         region.get('longitude', 0),
                         region.get('latitude', 0),
                         region.get('radius', 0),
                         region.get('points', ''),
                         region.get('shape', 0),
                         region.get('uid', ''))

        db.execute("INSERT INTO T_REGION_TERMINAL(rid, tid)"
                   "  VALUES(%s, %s)",
                   rid, region.get('tid', ''))
    else:  # create region for corp, and bind to terminal later.
        rid = db.execute("INSERT T_REGION(name, longitude, latitude,"
                         "  radius, points, shape, cid)"
                         "  VALUES(%s, %s, %s, %s, %s, %s, %s)",
                         region.get('region_name', ''),
                         region.get('longitude', 0),
                         region.get('latitude', 0),
                         region.get('radius', 0),
                         region.get('points', ''),
                         region.get('shape', 0),
                         region.get('cid', ''))
    return rid


def delete_region(region_ids, db, redis):
    """"Delete one or more regions.

    @arg region_ids: list, e.g.

        [
          xxx,
          yyy,
          ...
        ]

    @arg db: database instance
    @arg redis: redis instance

    """
    if not region_ids:
        return

    # 1: delete redis region status
    for region_id in region_ids:
        terminals = db.query("SELECT tid"
                             "  FROM T_REGION_TERMINAL"
                             "  WHERE rid = %s",
                             region_id)
        for terminal in terminals:
            region_status_key = get_region_status_key(terminal.tid, region_id)
            redis.delete(region_status_key)

    # 2: delete region, region event and region terminal relation
    db.execute("DELETE FROM T_REGION WHERE id IN %s",
               tuple(region_ids + DUMMY_IDS))

    db.execute("DELETE FROM T_EVENT WHERE rid IN %s",
               tuple(region_ids + DUMMY_IDS))

    db.execute("DELETE FROM T_REGION_TERMINAL WHERE rid IN %s",
               tuple(region_ids + DUMMY_IDS))

def bind_region(db, tids, region_ids):
    """Bind regions for some terminals.
    """
    sql = "DELETE FROM T_REGION_TERMINAL WHERE tid IN %s " % (
        tuple(tids + DUMMY_IDS_STR), )
    db.execute(sql)

    for tid in tids:
        for region_id in region_ids:
            db.execute("INSERT INTO T_REGION_TERMINAL(rid, tid)"
                       "  VALUES(%s, %s)",
                       region_id, tid)
    logging.info("[PUBLIC] Bind region. tids：%s, region_id: %s",
                 tids, region_id)


"""Part: Single.
"""


def add_single(single, db, redis):
    """"Add a single.

    :arg single: dict, e.g.

        {
          'region_name':'', 
          'longitude':'',
          'latitude':'',
          'radius':'',
          'points':'',
          'shape':'',
          'uid':'',
          'cid':'',
          'tid':'',
        }

    :arg db: database instance
    :arg redis: redis instance

    :arg single_id: int 

    """
    single_id = db.execute("INSERT T_SINGLE(name, longitude, latitude,"
                           "  radius, points, shape, cid)"
                           "  VALUES(%s, %s, %s, %s, %s, %s, %s)",
                           single.get('single_name', ''),
                           single.get('longitude', 0),
                           single.get('latitude', 0),
                           single.get('radius', 0),
                           single.get('points', ''),
                           single.get('shape', 0),
                           single.get('cid', ''))
    return single_id


def delete_single(single_ids, db, redis):
    """"Delete one or more regions.

    :arg single_ids: list, e.g.

        [
          xxx,
          yyy,
          ...
        ]

    :arg db: database instance
    :arg redis: redis instance

    """
    if not single_ids:
        return

    # 1: delete redis region status
    for single_id in single_ids:
        terminals = db.query("SELECT tid"
                             "  FROM T_SINGLE_TERMINAL"
                             "  WHERE sid = %s",
                             single_id)
        for terminal in terminals:
            single_status_key = get_single_status_key(
                terminal.tid, single_id)
            redis.delete(single_status_key)

    # 2: delete region, region event and region terminal relation
    db.execute("DELETE FROM T_SINGLE WHERE id IN %s",
               tuple(single_ids + DUMMY_IDS))

    # rid: region_id, single_id
    db.execute("DELETE FROM T_EVENT WHERE rid IN %s",
               tuple(single_ids + DUMMY_IDS))

    db.execute("DELETE FROM T_SINGLE_TERMINAL WHERE sid IN %s",
               tuple(single_ids + DUMMY_IDS))

def bind_single(db, tids, single_ids):
    """Bind singles for some terminals.
    """
    # NOTE: Clear the old data first.
    sql = "DELETE FROM T_SINGLE_TERMINAL WHERE tid IN %s " % (
        tuple(tids + DUMMY_IDS_STR), )
    db.execute(sql)

    # NOTE: Bind new single
    for tid in tids:
        for single_id in single_ids:
            db.execute("INSERT INTO T_SINGLE_TERMINAL(sid, tid)"
                       "  VALUES(%s, %s)",
                       single_id, tid)

"""Group
"""

def add_group(group, db, redis):
    """"Add a group.

    :arg single: dict, e.g.

        {
          'cid':'',
          'name':'',
          'type':'',
        }

    :arg db: database instance
    :arg redis: redis instance

    :arg gid: int 

    """
    gid = db.execute("INSERT T_GROUP(corp_id, name, type)"
                     "  VALUES(%s, %s, %s)",
                     group['cid'], group['name'], group['type'])
    return gid


"""Part: Features.
"""

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
    clear_sessionID(redis, tid)
    logging.info("[PUBLIC] Terminal update mannual_status. tid: %s, mannual_status: %s",
                 tid, mannual_status)

    record_manual_status(db, redis, tid, mannual_status)

# Feature: notify_maintainer


def notify_maintainer(db, redis, content, category):
    """Notify alarm info to maintainers.
    :arg category: int, e.g.
         1: gateway
         2: eventer
    """
    mobiles = []
    emails = []
    alarm_key = 'maintainer_alarm:%s' % category
    alarm_interval = 60 * 5  # 5 minutes

    alarm_flag = redis.getvalue(alarm_key)

    if not alarm_flag:
        maintainers = db.query(
            "SELECT mid, mobile, email FROM T_MAINTAINER WHERE valid = 1")

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

# Feature: update operator info


def update_operator(operator, oid, db, redis):
    """Update operator status.

    :arg operator: dict, e.g.

        {
          'address':'',
          'email':'',          
        }

    :arg oid: string
    :arg db: database instance
    :arg redis: redis instance

    """
    set_clause_dct = DotDict()
    fields = DotDict(address="address = '%s'",
                     email="email = '%s'")
    for key, value in operator.iteritems():
        set_clause_dct.setdefault(key, fields[key] % value)

    set_clause = ','.join(
        [v for v in set_clause_dct.itervalues() if v is not None])
    if set_clause:
        db.execute("UPDATE T_OPERATOR SET " + set_clause +
                   "  WHERE oid = %s",
                   oid)

# Feature: update corp info


def update_corp(corp, cid, db, redis):
    """Update corp status.

    :arg corp: dict, e.g.

        {
          'c_name':'',
          'c_mobile':'',          
          'c_alert_mobile':'',
          'c_address':'',
          'c_linkman':'',
          'c_email':'',
        }

    :arg cid: string
    :arg db: database instance
    :arg redis: redis instance

    """
    set_clause_dct = DotDict()
    fields = DotDict(c_name="name = '%s'",
                     c_mobile="mobile = '%s'",
                     c_alert_mobile="alert_mobile = '%s'",
                     c_address="address = '%s'",
                     c_linkman="linkman = '%s'",
                     c_email="email = '%s'")

    for key, value in corp.iteritems():
        set_clause_dct.setdefault(key, fields[key] % value)

    set_clause = ','.join(
        [v for v in set_clause_dct.itervalues() if v is not None])

    if set_clause:
        db.execute("UPDATE T_CORP SET " + set_clause +
                   "  WHERE cid = %s",
                   cid)


def update_alarm_option(alarm_option, uid, db, redis):
    """Update operator status.

    :arg alarm_option: dict, e.g.

        {
          'login':'',
          'powerlow':'', 
          ...         
        }

    :arg oid: string
    :arg db: database instance
    :arg redis: redis instance

    """
    set_clause_dct = DotDict()
    fields = DotDict(login="login = %s",
                     powerlow="powerlow = %s",
                     powerdown="powerdown = %s",
                     illegalshake="illegalshake = %s",
                     illegalmove="illegalmove = %s",
                     sos="sos = %s",
                     heartbeat_lost="heartbeat_lost = %s",
                     charge="charge = %s",
                     region_enter="region_enter = %s",
                     region_out="region_out = %s",
                     stop="stop = %s",
                     speed_limit="speed_limit = %s")

    for key, value in alarm_option.iteritems():
        alarm_option[key] = fields[key] % alarm_option[key]
        #set_clause_dct.setdefault(key, fields[key] % value)

    set_clause = ','.join(
        [v for v in alarm_option.itervalues() if v is not None])

    if set_clause:
        db.execute("UPDATE T_ALARM_OPTION SET " + set_clause +
                   "  WHERE uid = %s",
                   uid)


def update_speed_limit(speed_limit, tids, db):
    """Update operator status.

    :arg speed_limit: int
    :arg tid: string
    :arg db: database instance

    """
    db.executemany("UPDATE T_TERMINAL_INFO SET speed_limit = %s"
                   "  WHERE tid = %s",
                   [(speed_limit, tid) for tid in tids])

# Feature: restart terminal.


def restart_terminal(db, redis, tid, mobile):
    """Restart the terminal.
    """
    clear_sessionID(redis, tid)
    logging.info("[PUBLIC] Restart terminal. tid: %s, mobile: %s.",
                 tid, mobile)
    send_cq_sms(db, redis, tid, mobile)

def add_script(db, script):
    """Add lua script.
    """

    db.execute("INSERT INTO T_SCRIPT(version, filename, timestamp)"
               "  VALUES(%s, %s, %s)"
               "    ON DUPLICATE KEY"
               "    UPDATE version = VALUES(version),"
               "           filename = VALUES(filename),"
               "           timestamp = VALUES(timestamp)",
               script['versionname'], script['filename'], int(time.time()))

def kqly(db, redis, tids):
    """Start bluetooth.
    """
    for tid in tids:
        terminal = QueryHelper.get_terminal_by_tid(tid, db)
        kqly_key = get_kqly_key(tid)
        kqly_value = redis.getvalue(kqly_key)
        if not kqly_value:
            interval = 30  # in minute
            sms = SMSCode.SMS_KQLY % interval
            SMSHelper.send_to_terminal(terminal.mobile, sms)
            redis.setvalue(kqly_key, True, SMS.KQLY_SMS_INTERVAL)


def send_cq_sms(db, redis, tid, mobile):
    """Send cq sms to terminal..
    """
    sms_cq = SMSCode.SMS_CQ

    if len(mobile) != 11:
        logging.info("[PUBLIC] Mobile is valid, ignore it. mobile: %s", mobile)
        return

    biz_type = QueryHelper.get_biz_type_by_tmobile(mobile, db)
    if biz_type != UWEB.BIZ_TYPE.YDWS:
        logging.info(
            "[PUBLIC] Biz_type is no need cq, ignore it. mobile: %s, biz_type: %s", mobile, biz_type)
        return

    SMSHelper.send_to_terminal(mobile, sms_cq)
    logging.info("[PUBLIC] Send cq sms to terminal. mobile: %s", mobile)


def send_domain_sms(db, redis, tid, mobile, domain):
    """Send domain sms to terminal..
    """
    sms_domain = SMSCode.SMS_DOMAIN % domain
    SMSHelper.send_to_terminal(mobile, sms_domain)
    self.db.execute("UPDATE T_TERMINAL_INFO SET domain = %s"
                    "  WHERE tid = %s",
                    domain_ip, tid)
    logging.info("[PUBLIC] Send domain sms: %s to mobile: %s",
                 sms_domain, mobile)


def subscription_lbmp(mobile):
    """ Subscription LE for new sim.

    NOTE: deprecated. 
    In fact, subscription_lbmp can not work now.
    """
    data = DotDict(sim=mobile,
                   action="A")
    response = LbmpSenderHelper.forward(
        LbmpSenderHelper.URLS.SUBSCRIPTION, data)
    response = json_decode(response)
    if response['success'] == '000':
        logging.info("[GW] mobile: %s subscription LE success! ",
                     mobile)
    else:
        logging.info("[GW] mobile: %s subscription LE failed! response:%s",
                     mobile, response)

"""Part: Utils and others.
"""

def get_use_scene_by_vibl(vibl):
    """Get use_scene through vibl.

    :arg vibl: int

    :return use_scene: int

    """
    use_scene = 3 # default car scene
    if vibl == 1:
        use_scene = 3 # car
    elif vibl == 2:
        use_scene = 1 # moto car
    elif vibl == 3: 
        use_scene = 9 # human
    return use_scene

def generate_sessionID(redis, tid):
    """Genreate a sessionID and keep it in redis for the terminal.
    """
    sessionID = get_sessionID()
    terminal_sessionID_key = get_terminal_sessionID_key(tid)
    redis.setvalue(terminal_sessionID_key, sessionID)
    logging.info("[PUBLIC] Generate sessionID in redis. tid: %s.", tid)


def clear_sessionID(redis, tid):
    """Clear the sessionID associated with one terminal.
    """
    sessionID_key = get_terminal_sessionID_key(tid)
    redis.delete(sessionID_key)
    logging.info("[PUBLIC] Clear sessionID in redis. tid: %s.", tid)


def insert_location(location, db, redis):
    """Insert whole-data into T_LOCATION.
    """
    location = DotDict(location)
    # NOTE if locate_error is bigger then 500, set it 500
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
        # if track and (int(track) == 1) and (location.get("Tid", None) != EVENTER.TRIGGERID.PVT):
        #    return lid
        # NOTE: if location's type is gps, put it into redis
        if track and (int(track) == 1) and (location.type != 0):
            return lid

        location_key = get_location_key(location.dev_id)
        last_location = redis.getvalue(location_key)
        if (last_location and (location.gps_time > last_location['timestamp'])) or\
                not last_location:

            logging.info("[PUBLIC] Keep location in redis. tid: %s, location: %s",
                         location.dev_id, location)
            mem_location = {'id': lid,
                            'latitude': location.lat,
                            'longitude': location.lon,
                            'type': location.type,
                            'clatitude': location.cLat,
                            'clongitude': location.cLon,
                            'timestamp': location.gps_time,
                            'name': location.name,
                            'degree': location.degree,
                            'speed': location.speed,
                            'locate_error': location.locate_error}
            location_key = get_location_key(location.dev_id)
            redis.setvalue(location_key, mem_location, EVENTER.LOCATION_EXPIRY)

            if int(location.type) == 0:  # gps
                logging.info("[PUBLIC] Keep gps_location in gps_redis. tid: %s, location: %s",
                             location.dev_id, location)
                location_key = get_gps_location_key(location.dev_id)
                redis.setvalue(
                    location_key, mem_location, EVENTER.LOCATION_EXPIRY)

    return lid


def get_alarm_mobile(tid, db, redis):
    """Get the alarm mobile associate with the terminal.
    """
    alarm_mobile = ''
    t = db.get("SELECT cid FROM V_TERMINAL WHERE tid = %s LIMIT 1", tid)
    if t:
        cid = t.cid if t.get('cid', None) is not None else '0'
        corp = db.get(
            "SELECT name, alarm_mobile FROM T_CORP WHERE cid = %s", cid)
        if corp:
            alarm_mobile = corp['alarm_mobile']
    return alarm_mobile


def get_terminal_type_by_tid(tid):
    ttype = 'unknown'
    base = [str(x) for x in range(10)] + [chr(x)
                                          for x in range(ord('A'), ord('A') + 6)]
    try:
        tid_hex2dec = str(int(tid.upper(), 16))
    except:
        logging.info(
            "[PUBLIC] Terminal %s is illegale, can not transfer into 10 hexadecimal. It's type is unknown", tid)
        return ttype
    num = int(tid_hex2dec)
    mid = []
    while True:
        if num == 0:
            break
        num, rem = divmod(num, 2)
        mid.append(base[rem])
    bin_tid = ''.join([str(x) for x in mid[::-1]])
    l = 40 - len(bin_tid)
    s = '0' * l
    sn = s + bin_tid
    ttype = sn[15:18]
    if ttype == "000":
        ttype = 'zj100'
    elif ttype == '001':
        ttype = 'zj200'
    return ttype

def get_group_info_by_tid(db, tid):

    group_info = {'group_id': -1, 'group_name': ''}

    group = db.query("SELECT T_GROUP.id as group_id, T_GROUP.name as group_name FROM T_TERMINAL_INFO,T_GROUP"
                     "  WHERE T_TERMINAL_INFO.group_id = T_GROUP.id and tid = %s", tid)
    if group:
        group_info = group[0]

    return group_info

"""Part: Weixin.
"""


def get_weixin_push_key(uid, t):
    """Get key for push interface(register or push packet)"""
    secret = '7c2d6047c7ad95f79cdb985e26a92141'
    s = uid + str(t) + secret

    m = hashlib.md5()
    m.update(s)
    key = m.hexdigest()

    return key.decode('utf8')

"""Part: YDWQ.
"""


def update_terminal_info_ydwq(db, redis, t_info):
    """Update terminal's info in db and redis.
    """
    terminal_info_key = get_terminal_info_key(t_info['tid'])
    terminal_info = QueryHelper.get_terminal_info(t_info['tid'],
                                                  db, redis)

    # 1: db
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
    # 2: redis
    for key in terminal_info:
        value = t_info.get(key, None)
        if value is not None:
            terminal_info[key] = value
    redis.setvalue(terminal_info_key, terminal_info)

    return terminal_info


def update_terminal_status(redis, tid, address='DUMMY_ADDRESS'):
    terminal_status_key = get_terminal_address_key(tid)
    # 30 minuts
    redis.setvalue(
        terminal_status_key, address, GATEWAY.YDWQ_HEARTBEAT_INTERVAL)


def record_attendance(db, a_info):
    db.execute("INSERT INTO T_ATTENDANCE(mobile, comment, timestamp, lid)"
               "  VALUES(%s, %s, %s, %s)",
               a_info['mobile'], a_info['comment'], a_info['timestamp'], a_info['lid'])
