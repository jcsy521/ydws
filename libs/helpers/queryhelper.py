# -*- coding:utf-8 -*-

import time
import logging

from utils.misc import (get_terminal_info_key, get_lq_sms_key,
                        get_location_key, get_gps_location_key, get_login_time_key,
                        get_activation_code, get_acc_status_info_key, get_terminal_sessionID_key, DUMMY_IDS)
from utils.dotdict import DotDict
from constants import GATEWAY, EVENTER, UWEB


class QueryHelper(object):

    """A bunch of samll functions to get one attribute from another
    attribute in the db.
    """

    """Part: Terminal information.
    """

    @staticmethod
    def get_terminal_by_tid(tid, db):
        """Get terminal's info throught tid.
        """
        terminal = db.get("SELECT mobile, tid, owner_mobile, assist_mobile,"
                          "  dev_type, alias, login, biz_type, activation_code"
                          "  FROM T_TERMINAL_INFO"
                          "  WHERE tid = %s LIMIT 1",
                          tid)
        return terminal

    @staticmethod
    def get_terminal_by_tmobile(tmobile, db):
        """Get terminal info through tmobile.
        """
        terminal = db.get("SELECT tid, login, msgid, service_status, biz_type,"
                          "  activation_code, mobile"
                          "  FROM T_TERMINAL_INFO"
                          "  WHERE mobile = %s LIMIT 1",
                          tmobile)
        return terminal

    @staticmethod
    def get_terminal_by_activation_code(activation_code, db):
        """Get terminal info through activation_code.
        """
        terminal = db.get("SELECT id, service_status, mobile"
                          "  FROM T_TERMINAL_INFO"
                          "  WHERE activation_code = %s LIMIT 1",
                          activation_code)
        return terminal

    @staticmethod
    def get_terminals_by_uid(uid, biz_type, db):
        terminals = db.query("SELECT tid, mobile, owner_mobile, login, keys_num"
                             "    gsm, gps, pbat, login, defend_status, dev_type,"
                             "    mannual_status, fob_status, icon_type, bt_name, bt_mac"
                             "  FROM T_TERMINAL_INFO"
                             "  WHERE (service_status = %s"
                             "         OR service_status = %s)"
                             "    AND biz_type = %s"
                             "    AND owner_mobile = %s"
                             "    AND login_permit = 1"
                             "    ORDER BY LOGIN DESC",
                             UWEB.SERVICE_STATUS.ON,
                             UWEB.SERVICE_STATUS.TO_BE_ACTIVATED,
                             biz_type,
                             uid)
        return terminals

    @staticmethod
    def get_terminals_by_oid(oid, biz_type, db):

        groups = db.query(
            "SELECT group_id FROM T_GROUP_OPERATOR WHERE oper_id = %s", oid)
        gids = [g.group_id for g in groups]
        terminals = db.query("SELECT tid, mobile, owner_mobile, login, keys_num"
                             "    gsm, gps, pbat, login, defend_status, dev_type,"
                             "    mannual_status, fob_status, icon_type, bt_name, bt_mac"
                             "  FROM T_TERMINAL_INFO"
                             "  WHERE (service_status = %s"
                             "         OR service_status = %s)"
                             "    AND biz_type = %s"
                             "    AND group_id IN %s"
                             "    ORDER BY LOGIN DESC",
                             UWEB.SERVICE_STATUS.ON,
                             UWEB.SERVICE_STATUS.TO_BE_ACTIVATED,
                             biz_type,
                             tuple(DUMMY_IDS + gids))
        return terminals

    @staticmethod
    def get_terminals_by_cid(cid, biz_type, db):

        groups = db.query(
            "SELECT id gid, name FROM T_GROUP WHERE corp_id = %s", cid)
        gids = [g.gid for g in groups]
        terminals = db.query("SELECT tid, mobile, owner_mobile, login, keys_num"
                             "    gsm, gps, pbat, login, defend_status, dev_type,"
                             "    mannual_status, fob_status, icon_type, bt_name, bt_mac"
                             "  FROM T_TERMINAL_INFO"
                             "  WHERE (service_status = %s"
                             "         OR service_status = %s)"
                             "    AND biz_type = %s"
                             "    AND group_id IN %s"
                             "    ORDER BY LOGIN DESC",
                             UWEB.SERVICE_STATUS.ON,
                             UWEB.SERVICE_STATUS.TO_BE_ACTIVATED,
                             biz_type,
                             tuple(DUMMY_IDS + gids))
        return terminals

    @staticmethod
    def get_tmobile_by_tid(tid, redis, db):
        terminal_info_key = get_terminal_info_key(tid)
        terminal_info = redis.getvalue(terminal_info_key)
        if terminal_info:
            if terminal_info.mobile:
                return terminal_info.mobile

        terminal = QueryHelper.get_terminal_by_tid(tid, db)
        mobile = terminal.mobile if terminal else None

        return mobile

    @staticmethod
    def get_alias_by_tid(tid, redis, db):
        """Get a readable alias  throught tid.
        workflow:
        if alias exists in redis:
            return alias 
        else:
            if cnum in db:
                alias = cnum 
            else: 
                alias = sim
        return alias 
        """
        terminal_info_key = get_terminal_info_key(tid)
        terminal_info = redis.getvalue(terminal_info_key)
        if terminal_info:
            if terminal_info.alias:
                return terminal_info.alias

        car = db.get("SELECT cnum FROM T_CAR"
                     "  WHERE tid = %s LIMIT 1",
                     tid)
        if car and car.cnum:
            alias = car.cnum
        else:
            terminal = QueryHelper.get_terminal_by_tid(tid, db)
            alias = terminal.mobile

        return alias

    @staticmethod
    def get_cnum_by_terminal(tid, tmobile, redis, db):

        cnum = ''
        car = db.get("SELECT cnum FROM T_CAR WHERE tid = %s", tid)
        if car and car['cnum']:
            cnum = car['cnum']
        else:
            car = db.get("SELECT cnum FROM T_CAR WHERE tid = %s", tmobile)
            if car and car['cnum']:
                cnum = car['cnum']
        return cnum

    @staticmethod
    def get_biz_by_mobile(mobile, db):
        """Get user info through tmobile.
        """
        biz = db.get("SELECT biz_type"
                     "  FROM T_BIZ_WHITELIST"
                     "  WHERE mobile = %s LIMIT 1",
                     mobile)
        return biz

    @staticmethod
    def get_white_list_by_tid(tid, db):
        """Get white list through tid.
        """
        whitelist = db.query("SELECT mobile"
                             "  FROM T_WHITELIST"
                             "  WHERE tid = %s LIMIT 1",
                             tid)
        return whitelist

    @staticmethod
    def get_fob_list_by_tid(tid, db):
        """Get fob list through tid.
        """
        foblist = db.query("SELECT fobid"
                           "  FROM T_FOB"
                           "  WHERE tid = %s",
                           tid)
        return foblist

    @staticmethod
    def get_mannual_status_by_tid(tid, db):
        """Get tracker's mannual status.
        """
        mannual_status = None
        t = db.get("SELECT mannual_status"
                   "  FROM T_TERMINAL_INFO"
                   "  WHERE tid = %s",
                   tid)
        if t:
            mannual_status = t['mannual_status']

        return mannual_status

    @staticmethod
    def get_terminal_info(tid, db, redis):
        """Get tracker's terminal info.
        """
        terminal_info_key = get_terminal_info_key(tid)
        terminal_info = redis.getvalue(terminal_info_key)
        if not terminal_info:
            terminal_info = db.get("SELECT mannual_status, defend_status,"
                                   "  fob_status, mobile, owner_mobile, login, gps, gsm,"
                                   "  pbat, keys_num, icon_type, softversion, bt_name, bt_mac,"
                                   "  assist_mobile, distance_current, dev_type, biz_type"
                                   "  FROM T_TERMINAL_INFO"
                                   "  WHERE tid = %s", tid)
            car = db.get("SELECT cnum FROM T_CAR"
                         "  WHERE tid = %s", tid)
            fobs = db.query("SELECT fobid FROM T_FOB"
                            "  WHERE tid = %s", tid)
            if car:
                terminal_info[
                    'alias'] = car.cnum if car.cnum else terminal_info.mobile
            else:
                terminal_info['alias'] = terminal_info.mobile
            terminal_info['fob_list'] = [fob.fobid for fob in fobs]

            if terminal_info['login'] == GATEWAY.TERMINAL_LOGIN.SLEEP:
                terminal_info['login'] = GATEWAY.TERMINAL_LOGIN.ONLINE

            redis.setvalue(terminal_info_key, terminal_info)

        return terminal_info

    @staticmethod
    def get_terminal_basic_info(tid, db):
        """Get tracker's terminal basic info.

        @return: res, {'tid':'',
                       'tmobile':'',
                       'umobile':'',
                       'group_id':'',
                       'oid':[],
                       'cid':''}
        """
        res = {}
        terminal = db.get("SELECT tid, mobile, owner_mobile, group_id"
                          "  FROM T_TERMINAL_INFO WHERE tid = %s", tid)
        if terminal:
            cid = ''
            oid = []
            group = db.get("SELECT corp_id FROM T_GROUP WHERE id = %s",
                           terminal['group_id'])
            if group:
                cid=group.get('corp_id', '') 
                oper = db.query("SELECT oper_id"
                       "  FROM T_GROUP_OPERATOR "
                       "  WHERE group_id = %s",
                       terminal['group_id'])
                if oper:
                    oid = [item.oper_id for item in oper]
            res = dict(tid=terminal['tid'],
                       tmobile=terminal['mobile'],
                       umobile=terminal['owner_mobile'],
                       group_id=terminal['group_id'],
                       cid=cid,
                       oid=oid)
        return res

    @staticmethod
    def get_available_terminal(tid, db):
        """Get available terminal.
        """
        terminal = db.get("SELECT id, freq, alias, trace, cellid_status,"
                          "       vibchk, tid as sn, mobile, vibl, move_val, "
                          "       static_val, alert_freq, login,"
                          "       white_pop, push_status, icon_type, owner_mobile, "
                          "       login_permit, stop_interval, biz_type, speed_limit,"
                          "       mannual_status, fob_status"
                          "  FROM T_TERMINAL_INFO"
                          "  WHERE tid = %s"  # trim(tid)
                          "    AND (service_status = %s"
                          "    OR service_status = %s)"
                          "  LIMIT 1",
                          tid, UWEB.SERVICE_STATUS.ON,
                          UWEB.SERVICE_STATUS.TO_BE_ACTIVATED)
        return terminal

    @staticmethod
    def get_login_time_by_tid(tid, db, redis):
        """Get tracker's login_time.
        """
        login_time_key = get_login_time_key(tid)
        login_time = redis.get(login_time_key)
        if not login_time:
            t = db.get("SELECT login_time FROM T_TERMINAL_INFO"
                       "  WHERE tid = %s LIMIT 1",
                       tid)
            login_time = t.login_time
            redis.set(login_time_key, login_time)

        return int(login_time)

    @staticmethod
    def get_all_terminals_by_cid(cid, db):
        """Get all trackers belongs to a corp.
        """
        terminals = db.query("SELECT tt.mobile, tt.owner_mobile, tt.tid"
                             "  FROM T_TERMINAL_INFO as tt, T_GROUP as tg, T_CORP as tc"
                             "  WHERE (tt.service_status = %s"
                             "     OR tt.service_status = %s)"
                             "  AND tc.cid = %s "
                             "  AND tc.cid = tg.corp_id "
                             "  AND tt.group_id = tg.id",
                             UWEB.SERVICE_STATUS.ON,
                             UWEB.SERVICE_STATUS.TO_BE_ACTIVATED,
                             cid)
        return terminals

    @staticmethod
    def get_all_terminals_by_oid(oid, db):
        """Get all trackers belongs to a operator.
        """
        terminals = db.query("SELECT mobile, owner_mobile, tid FROM T_TERMINAL_INFO "
                             "  WHERE (service_status = %s"
                             "    OR service_status = %s)"
                             "  AND group_id IN"
                             "    (SELECT group_id FROM T_GROUP_OPERATOR"
                             "     WHERE T_GROUP_OPERATOR.oper_id = %s)",
                             UWEB.SERVICE_STATUS.ON,
                             UWEB.SERVICE_STATUS.TO_BE_ACTIVATED,
                             oid)
        return terminals

    @staticmethod
    def get_terminals_by_group_id(group_id, db):
        """Get all trackers belongs to a group_id.
        """
        terminals = db.query("SELECT tid FROM T_TERMINAL_INFO"
                             "  WHERE group_id = %s"
                             "    AND (service_status = %s"
                             "    OR service_status = %s)",
                             group_id, UWEB.SERVICE_STATUS.ON,
                             UWEB.SERVICE_STATUS.TO_BE_ACTIVATED)
        return terminals

    @staticmethod
    def get_biz_type_by_tmobile(tmobile, db):
        terminal = db.get("SELECT biz_type FROM T_TERMINAL_INFO"
                          "  WHERE mobile = %s LIMIT 1",
                          tmobile)
        biz_type = terminal.get('biz_type', None) if terminal else None
        return biz_type

    @staticmethod
    def get_version_info_by_category(category, db):
        version_info = db.get("SELECT versioncode, versionname, versioninfo, updatetime, filesize, filename"
                              "  FROM T_APK"
                              "  WHERE category = %s"
                              "  ORDER BY id DESC LIMIT 1",
                              category)
        if version_info:
            version_info['filesize'] = '%sM' % version_info['filesize']
            version_info['filepath'] = '/static/apk/' + \
                version_info['filename']

        return version_info if version_info else {'versioncode': 0}

    @staticmethod
    def get_service_status_by_tmobile(db, mobile):
        service_status = UWEB.SERVICE_STATUS.ON
        biz_type = QueryHelper.get_biz_type_by_tmobile(mobile, db)
        if biz_type == UWEB.BIZ_TYPE.YDWQ:
            terminal = db.get("SELECT tid, mobile, service_status FROM T_TERMINAL_INFO"
                              "  WHERE mobile = %s"
                              "  AND biz_type = %s LIMIT 1",
                              mobile, UWEB.BIZ_TYPE.YDWQ)

            service_status = terminal['service_status']
        return service_status

    @staticmethod
    def get_ajt_whitelist_by_mobile(mobile, db):
        """Get ajt whitelist through mobile.
        """
        biz = db.get("SELECT id, mobile, timestamp"
                     "  FROM T_AJT_WHITELIST"
                     "  WHERE mobile = %s LIMIT 1",
                     mobile)
        return biz

    @staticmethod
    def get_mileage_notification_by_tid(tid, db):
        """Get mileage notification infomation according to tid.
        """
        mileage = DotDict()
        res = db.get("SELECT owner_mobile, assist_mobile, distance_current"
                     "  FROM T_TERMINAL_INFO"
                     "  WHERE tid = %s limit 1",
                     tid)
        mileage.update(res)

        mileage_res = db.get("SELECT distance_notification"
                             "  FROM T_MILEAGE_NOTIFICATION"
                             "  WHERE tid = %s LIMIT 1",
                             tid)
        if mileage_res:
            mileage.update(mileage_res)
        else:
            db.execute("INSERT INTO T_MILEAGE_NOTIFICATION(tid) "
                       "  VALUES(%s)",
                       tid)
            mileage.update({'distance_notification': 0})

        day_res = db.get("SELECT day_notification"
                         "  FROM T_DAY_NOTIFICATION"
                         "  WHERE tid = %s LIMIT 1",
                         tid)
        if day_res:
            mileage.update(day_res)
        else:
            db.execute("INSERT INTO T_DAY_NOTIFICATION(tid) "
                       "  VALUES(%s)",
                       tid)
            mileage.update({'day_notification': 0})

        return mileage

    @staticmethod
    def get_acc_status_info_by_tid(client_id, tid, db, redis):
        """Get acc status infomation according to tid.

        :arg client_id: string
        :arg tid: string
        :arg db: database instance
        :arg redis: redis instance

        :return acc_status_info：dict, 6 items. e.g.
        { 
            client_id: unique id of a login on of a user,
            op_type 1: power on (default), 0: power off 
            timestamp: the operate option
            op_status: 1: success, 0: failed(time out), 2: to be query by T2
            t2_status: 1: T2 query occurs. 2: wait for T2. 
            acc_message: notify message.

        }

        NOTE: 
        1. acc_status just record the action occurs in platform, for power
        status is maybe modified by fob or others, so it does not represent
        the newest power status in tracker.

        """

        acc_status_info_key = get_acc_status_info_key(tid)
        acc_status_info = redis.getvalue(acc_status_info_key)
        if not acc_status_info:
            # provide a default dict.
            acc_status_info = dict(client_id=client_id,
                                   op_type=1,
                                   timestamp=0,
                                   op_status=0,
                                   t2_status=0,
                                   acc_message=u'')
            # logging.info("[QUERYHELPER] Termianl does not has acc_status_info, current_id: %s, tid: %s ",
            #             client_id, tid)
        else:  # a whole dict should be found
            acc_action = u'锁定' if acc_status_info['op_type'] else u'解锁'
            terminal_info = QueryHelper.get_terminal_info(tid, db, redis)
            alias = terminal_info['alias']
            if acc_status_info['client_id'] != client_id:
                logging.info("[QUERYHELPER] Current client_id is not match acc_status, renturn nothing, "
                             "current_id: %s, acc_status_info: %s",
                             client_id, acc_status_info)
            else:
                if acc_status_info['op_status']:
                    acc_status_info['acc_message'] = '1'
                    # acc_status_info['acc_message'] = ''.join([alias, acc_action, u'成功'])
                    redis.delete(acc_status_info_key)
                    logging.info("[QUERYHELPER] Termianl does receive terminal's response, set successful. current_id: %s, tid: %s",
                                 client_id, tid)
                else:
                    # NOTE: acc_status_info['timestamp'] should never be 0
                    if int(time.time()) - acc_status_info['timestamp'] > 90:
                        acc_status_info['acc_message'] = '0'
                        # acc_status_info['acc_message'] = ''.join([alias, acc_action, u'失败'])
                        redis.delete(acc_status_info_key)
                        logging.info("[QUERYHELPER] Termianl does not receive terminal's response in 4 minutes, set failed. current_id: %s, tid: %s",
                                     client_id, tid)
                    else:
                        logging.info("[QUERYHELPER] Termianl does not receive terminal's respons, just wait, current_id: %s, tid: %s ",
                                     client_id, tid)
                        pass

        return acc_status_info

    @staticmethod
    def get_car_by_tid(tid, db):
        """Get car info of a terminal.

        :arg tid: string
        :arg db: database instance

        :return car: dict, e.g.

            {
              'cnum':''
            }

        """
        car = db.get("SELECT cnum FROM T_CAR"
                     "  WHERE tid = %s",
                     tid)
        if not car:
            db.execute("INSERT INTO T_CAR(tid)"
                       "  VALUES(%s)",
                       tid)
            car = db.get("SELECT cnum FROM T_CAR"
                         "  WHERE tid = %s",
                         tid)
        return car

    @staticmethod
    def get_bind_region(tid, db):
        """Get binded regions of a terminal.

        :arg tid: string
        :arg db: database instance

        :return res: dict, e.g.

            {
              'region_id':''
            }

        """

        res = db.query("SELECT tr.id AS region_id"
                       "  FROM T_REGION tr, T_REGION_TERMINAL trt"
                       "  WHERE tr.id = trt.rid"
                       "  AND trt.tid = %s",
                       tid)
        return res

    @staticmethod
    def get_bind_single(tid, db):
        """Get binded singles of a terminal.

        :arg tid: string
        :arg db: database instance

        :return res: dict, e.g.

            {
              'single_id':''
            }
        """

        res = db.query("SELECT ts.id AS single_id"
                       "  FROM T_SINGLE ts, T_SINGLE_TERMINAL tst"
                       "  WHERE ts.id = tst.sid"
                       "  AND tst.tid = %s",
                       tid)
        return res

    """Part: User, operator, corp information.
    """

    @staticmethod
    def get_user_by_tid(tid, db):
        """Get user info through tid.
        """
        user = db.get("SELECT owner_mobile"
                      "  FROM T_TERMINAL_INFO"
                      "  WHERE tid = %s LIMIT 1",
                      tid)
        return user

    @staticmethod
    def get_user_by_uid(uid, db):
        user = db.get("SELECT mobile, name, email, openid"
                      "  FROM T_USER"
                      "  WHERE uid= %s LIMIT 1",
                      uid)
        return user

    @staticmethod
    def get_user_by_mobile(mobile, db):
        """Get user info throught tmobile.
        """
        user = db.get("SELECT id, mobile, name"
                      "  FROM T_USER"
                      "  WHERE mobile = %s LIMIT 1",
                      mobile)
        return user

    @staticmethod
    def get_corp_by_cid(cid, db):
        corp = db.get("SELECT name c_name, mobile c_mobile, alert_mobile c_alert_mobile,"
                      " address c_address, email c_email, linkman c_linkman, bizcode"
                      "  FROM T_CORP"
                      "  WHERE cid = %s"
                      "  LIMIT 1",
                      cid)
        return corp

    @staticmethod
    def get_corp_by_oid(oid, db):
        corp = db.get("SELECT tc.cid, tc.mobile, tc.name, tc.linkman, tc.bizcode"
                      "  FROM T_CORP AS tc, T_OPERATOR AS toper"
                      "  WHERE toper.oid= %s"
                      "    AND toper.corp_id = tc.cid",
                      oid)
        return corp

    @staticmethod
    def get_corp_by_gid(gid, db):
        if int(gid) == -1:
            corp = None
        else:
            corp = db.get("SELECT tc.cid, tc.mobile, tc.name, tc.linkman, tc.bizcode"
                          "  FROM T_CORP AS tc, T_GROUP AS tg"
                          "  WHERE tg.id= %s"
                          "    AND tg.corp_id = tc.cid",
                          gid)
        return corp

    @staticmethod
    def get_operator_by_oid(oid, db):
        operator = db.get("SELECT name, mobile, address, email"
                          "  FROM T_OPERATOR"
                          "  WHERE oid = %s"
                          "  LIMIT 1",
                          oid)
        return operator

    @staticmethod
    def get_user_by_tmobile(tmobile, db):
        """Get user info throught tmobile.
        """
        user = db.get("SELECT owner_mobile"
                      "  FROM T_TERMINAL_INFO"
                      "  WHERE mobile = %s LIMIT 1",
                      tmobile)
        return user

    @staticmethod
    def get_corp_by_groupid(groupid, db):
        corp = DotDict()
        res = db.get("SELECT tc.cid, tc.name FROM T_GROUP AS tg, T_CORP AS tc"
                     "  WHERE tg.corp_id = tc.cid"
                     "  AND tg.id = %s",
                     groupid)
        if res:
            corp.name = res['name']
            corp.cid = res['cid']

        return corp

    @staticmethod
    def get_default_group_by_cid(cid, db):
        group = DotDict()
        res = db.get("SELECT id, name from T_GROUP"
                     "  WHERE corp_id = %s"
                     "  AND type=0 LIMIT 1",
                     cid)
        if res:
            group.name = res['name']
            group.gid = res['id']
        else:
            gid = db.execute("INSERT INTO T_GROUP(corp_id)"
                             "  values(%s)",
                             cid)
            group.name = u'默认组'
            group.gid = gid
        return group

    @staticmethod
    def get_groups_by_cid(cid, db):
        """Get groups belong to the corp.
        """

        groups = db.query("SELECT id AS gid, name, type"
                       "  FROM T_GROUP"
                       "  WHERE corp_id = %s",
                       cid)
        return groups

    @staticmethod
    def get_uid_by_tid(tid, db):
        uid = db.get(
            "SELECT owner_mobile FROM T_TERMINAL_INFO WHERE tid = %s", tid)
        return uid["owner_mobile"]

    """Part: SMS_option information.
    """

    @staticmethod
    def get_sms_option(uid, db):
        """Get sms options of a user.
        @param: uid,
                db
        @return: sms_options
        """
        sms_options = db.get("SELECT login, powerlow, powerdown, illegalshake,"
                             "  illegalmove, sos, heartbeat_lost, charge, "
                             "  region_enter, region_out, speed_limit"
                             "  FROM T_SMS_OPTION"
                             "  WHERE uid = %s"
                             "  LIMIT 1",
                             uid)
        if not sms_options:
            db.execute("INSERT INTO T_SMS_OPTION(uid)"
                       "  VALUES(%s)",
                       uid)
            sms_options = db.get("SELECT login, powerlow, powerdown, illegalshake,"
                                 "  illegalmove, sos, heartbeat_lost, charge, "
                                 "  region_enter, region_out, speed_limit"
                                 "  FROM T_SMS_OPTION"
                                 "  WHERE uid = %s"
                                 "  LIMIT 1",
                                 uid)
        return sms_options

    @staticmethod
    def get_sms_option_by_uid(uid, category, db):
        """Get sms options of a user.
        @param: uid,
                category,
                db
        @return: sms_option, // int. 1: send sms; 0: do not send sms
        """
        sms_option = db.get("SELECT " + category +
                            "  FROM T_SMS_OPTION"
                            "  WHERE uid = %s",
                            uid)
        if not sms_option:
            db.execute("INSERT INTO T_SMS_OPTION(uid)"
                       "  VALUES(%s)",
                       uid)
            sms_option = db.get("SELECT " + category +
                                "  FROM T_SMS_OPTION"
                                "  WHERE uid = %s",
                                uid)
        return sms_option[category]

    """Part: Alarm options information.
    """
    @staticmethod
    def get_alarm_options(uid, db):
        """Get alarm options of a user.

        :arg uid: string
        :arg db: database instance

        :return alarm_options: dict.

        """
        alarm_options = db.get("SELECT login, powerlow, powerdown, illegalshake,"
                               "    illegalmove, sos, heartbeat_lost, charge, "
                               "    region_enter, region_out, stop, speed_limit"
                               "  FROM T_ALARM_OPTION"
                               "  WHERE uid = %s"
                               "  LIMIT 1",
                               uid)
        if not alarm_options:
            db.execute("INSERT INTO T_ALARM_OPTION(uid)"
                       "  VALUES(%s)",
                       uid)

            alarm_options = db.get("SELECT login, powerlow, powerdown, illegalshake,"
                                   "    illegalmove, sos, heartbeat_lost, charge, "
                                   "    region_enter, region_out, stop, speed_limit"
                                   "  FROM T_ALARM_OPTION"
                                   "  WHERE uid = %s"
                                   "  LIMIT 1",
                                   uid)
        return alarm_options

    """Part: Region information.
    """

    @staticmethod
    def get_regions(tid, db):
        """Get all regions associated with the tid."""
        regions = db.query("SELECT tr.id AS region_id, tr.name AS region_name, "
                           "       tr.longitude AS region_longitude, tr.latitude AS region_latitude, "
                           "       tr.radius AS region_radius,"
                           "       tr.points, tr.shape AS region_shape"
                           "  FROM T_REGION tr, T_REGION_TERMINAL trt "
                           "  WHERE tr.id = trt.rid"
                           "  AND trt.tid = %s",
                           tid)
        return regions

    @staticmethod
    def get_regions_by_cid(cid, db):
        """Get all regions associated with the cid."""

        regions = db.query("SELECT id AS region_id, name AS region_name,"
                           "       longitude, latitude, radius,"
                           "       points, shape AS region_shape"
                           "  FROM T_REGION"
                           "  WHERE cid = %s",
                           cid)
        return regions

    @staticmethod
    def get_region(rid, db):
        """Get single info through single_id.
        """
        region = db.get("SELECT id AS region_id, name AS region_name, longitude, latitude,"
                        "  radius, points, shape AS region_shape"
                        "  FROM T_REGION"
                        "  WHERE id = %s",
                        rid)
        return region

    """Part: Single information.
    """

    @staticmethod
    def get_singles(tid, db):
        """Get all singles associated with the tid."""
        singles = db.query("SELECT ts.id AS single_id, ts.name AS single_name, "
                           "       ts.longitude AS single_longitude, ts.latitude AS single_latitude, "
                           "       ts.radius AS single_radius,"
                           "       ts.points, ts.shape AS single_shape"
                           "  FROM T_SINGLE ts, T_SINGLE_TERMINAL tst "
                           "  WHERE ts.id = tst.sid"
                           "  AND tst.tid = %s",
                           tid)
        return singles

    @staticmethod
    def get_singles_by_cid(cid, db):
        """Get all singles associated with the cid."""
        singles = db.query("SELECT id AS single_id, name AS single_name,"
                           "       longitude, latitude, radius,"
                           "       points, shape AS single_shape"
                           "  FROM T_SINGLE"
                           "  WHERE cid = %s",
                           cid)

        return singles

    @staticmethod
    def get_single(single_id, db):
        """Get single info through single_id.
        """
        single = db.get("SELECT id AS single_id, name AS single_name, longitude, latitude,"
                        "  radius, points, shape AS single_shape"
                        "  FROM T_SINGLE"
                        "  WHERE id = %s",
                        single_id)
        return single

    @staticmethod
    def get_single_event_by_se_id(se_id, db):
        """Get single-events info through se_id.
        """
        single_event = db.get("SELECT sid, tid, start_time, end_time"
                              "  FROM T_SINGLE_EVENT"
                              "  WHERE id = %s",
                              se_id)
        return single_event

    """Part: Location information.
    """

    @staticmethod
    def get_location_info(tid, db, redis):
        """Get tracker's last location and keep a copy in redis.
        """
        location_key = get_location_key(str(tid))
        location = redis.getvalue(location_key)
        if not location:
            # location = db.get("SELECT id, speed, timestamp, category, name,"
            #                  "  degree, type, latitude, longitude, clatitude, clongitude,"
            #                  "  timestamp, locate_error"
            #                  "  FROM T_LOCATION"
            #                  "  WHERE tid = %s"
            #                  "    AND NOT (latitude = 0 AND longitude = 0)"
            #                  "    ORDER BY timestamp DESC"
            #                  "    LIMIT 1",
            #                  tid)
            if location:
                mem_location = DotDict({'id': location.id,
                                        'latitude': location.latitude,
                                        'longitude': location.longitude,
                                        'type': location.type,
                                        'clatitude': location.clatitude,
                                        'clongitude': location.clongitude,
                                        'timestamp': location.timestamp,
                                        'name': location.name,
                                        'degree': float(location.degree),
                                        'speed': float(location.speed),
                                        'locate_error': int(location.locate_error)})

                redis.setvalue(
                    location_key, mem_location, EVENTER.LOCATION_EXPIRY)

        # NOTE: if locate_error is bigger than 500, set it as 500
        if location and int(location['locate_error']) > 500:
            location['locate_error'] = 500

        if location:
            location['speed'] = int(round(location['speed'])) 
        
        return location

    @staticmethod
    def get_gps_location_info(tid, db, redis):
        """Get tracker's last location and keep a copy in redis.
        """
        location_key = get_gps_location_key(str(tid))
        location = redis.getvalue(location_key)
        if not location:
            # location = db.get("SELECT id, speed, timestamp, category, name,"
            #                  "  degree, type, latitude, longitude, clatitude, clongitude,"
            #                  "  timestamp, locate_error"
            #                  "  FROM T_LOCATION"
            #                  "  WHERE tid = %s"
            #                  "    AND type = 0"
            #                  "    AND NOT (latitude = 0 AND longitude = 0)"
            #                  "    ORDER BY timestamp DESC"
            #                  "    LIMIT 1",
            #                  tid)
            if location:
                mem_location = DotDict({'id': location.id,
                                        'latitude': location.latitude,
                                        'longitude': location.longitude,
                                        'type': location.type,
                                        'clatitude': location.clatitude,
                                        'clongitude': location.clongitude,
                                        'timestamp': location.timestamp,
                                        'name': location.name,
                                        'degree': float(location.degree),
                                        'speed': float(location.speed),
                                        'locate_error': int(location.locate_error)})

                redis.setvalue(
                    location_key, mem_location, EVENTER.LOCATION_EXPIRY)
        return location

    """Part: Activity.
    """

    @staticmethod
    def get_terminal_sessionID(tid, redis):
        terminal_sessionID_key = get_terminal_sessionID_key(tid)
        # NOTE: eval is issued in getvalue method, if session contains 'e', the
        # sessionid may becomes a float,  so use get method here.
        sessionID = redis.get(terminal_sessionID_key)
        return sessionID

    @staticmethod
    def get_activity_list(db):
        """Get activities list.

        :arg db: database instance
        """
        res = db.query("SELECT title, begintime, endtime, filename, html_name"
                       "  FROM T_ACTIVITY"
                       "  ORDER BY begintime DESC")
        return res

    @staticmethod
    def get_activity_avaliable(db):
        """Get activities which are available till now.

        :arg db: database instance
        """
        res = db.query("SELECT title, begintime, endtime, filename, html_name"
                       "  FROM T_ACTIVITY"
                       "  WHERE endtime > %s",
                       int(time.time()))
        return res

    @staticmethod
    def get_activity_by_begintime(begintime, db):
        """Get activities which are begin after the `begintime`.

        :arg begintime: utc time. in second.
        :arg db: database instance

        """
        res = db.query("SELECT title, begintime, endtime, filename, html_name"
                       "  FROM T_ACTIVITY"
                       "  WHERE begintime > %s",
                       begintime)
        return res

    """Part: Get data, and data paged.
    """

    @staticmethod
    def get_single_event(tid, start_time, end_time, db):
        """Get the single_event between `start_time` and `end_time`.    

        :arg tid: string
        :arg start_time: utc time. in second
        :arg end_time: utc time. in second
        :arg db: database instance

        """
        res = db.get("SELECT COUNT(*) AS count"
                     "  FROM T_SINGLE_EVENT AS tse, T_SINGLE AS ts"
                     "  WHERE tse.tid = %s"
                     "  AND tse.sid = ts.id"
                     "  AND end_time != 0"
                     "  AND (start_time between %s and %s)",
                     tid, start_time, end_time)
        return res

    @staticmethod
    def get_single_event_paged(tid, start_time, end_time, offset, rows, db):
        """Get the single_event between `start_time` and `end_time`.    

        :arg tid: string
        :arg start_time: utc time. in second
        :arg end_time: utc time. in second
        :arg offset: int
        :arg rows: int
        :arg db: database instance

        """
        res = db.query("SELECT tse.id AS se_id, tse.start_time, tse.end_time,"
                       "    ts.id AS single_id, ts.name AS single_name"
                       "  FROM T_SINGLE_EVENT AS tse, T_SINGLE AS ts"
                       "  WHERE tse.tid = %s"
                       "  AND tse.sid = ts.id"
                       "  AND end_time != 0"
                       "  AND (start_time between %s and %s)"
                       "  LIMIT %s, %s",
                       tid, start_time, end_time,
                       offset, rows)
        return res

    @staticmethod
    def get_announcement(cid, start_time, end_time, db):
        """Get the announcement between `start_time` and `end_time`.    

        :arg tid: string
        :arg start_time: utc time. in second
        :arg end_time: utc time. in second
        :arg db: database instance

        """
        res = db.get("SELECT COUNT(*) AS count"
                     "  FROM T_ANNOUNCEMENT_LOG"
                     "  WHERE umobile = %s "
                     "  AND (timestamp BETWEEN %s AND %s)",
                     cid, start_time, end_time)
        return res

    @staticmethod
    def get_announcement_paged(cid, start_time, end_time, offset, rows, db):
        """Get the announcement between `start_time` and `end_time`.    

        :arg cid: string
        :arg start_time: utc time. in second
        :arg end_time: utc time. in second
        :arg offset: int
        :arg rows: int
        :arg db: database instance

        """
        res = db.query("SELECT id, umobile, content, timestamp, mobiles"
                       "  FROM T_ANNOUNCEMENT_LOG"
                       "  WHERE umobile = %s"
                       "  AND (timestamp BETWEEN %s AND %s)"
                       "  ORDER BY timestamp DESC"
                       "  LIMIT %s, %s",
                       cid,
                       start_time, end_time,
                       offset, rows)
        return res

    """Part: Utils information and others.
    """

    @staticmethod
    def get_alert_freq_by_tid(tid, db):
        """Get tracker's alert_freq.
        """
        alert_freq = db.get(
            "SELECT alert_freq FROM T_TERMINAL_INFO WHERE tid=%s", tid)
        return int(alert_freq['alert_freq'])

    @staticmethod
    def get_activation_code(db):
        """Generate a actiation_code which is never been used in db.

        workflow:
        for i in 0~9: # try it at most 10 times
            try to get a actiation_code
            if actiation_code is valid:
                return it
            else:
                continue to try
        """
        activation_code = ''
        times = 10
        for i in range(times):
            activation_code = get_activation_code()
            t = db.get("SELECT id FROM T_TERMINAL_INFO WHERE activation_code = %s LIMIT 1",
                       activation_code)
            if not t:
                break
            else:
                activation_code = ''
        if not activation_code:
            logging.error("[QUERYHELPER] After times: %s, there is not a invalid actiation_code is got, have a check!",
                          times)
        return activation_code
