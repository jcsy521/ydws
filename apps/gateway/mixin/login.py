# -*- coding: utf-8 -*-

import logging
import time

from clw.packet.parser.login import LoginParser
from clw.packet.composer.login import LoginRespComposer

from utils.checker import check_phone, check_zs_phone
from utils.dotdict import DotDict
from codes.smscode import SMSCode

from utils.misc import (get_resend_key, get_sessionID, 
     get_terminal_sessionID_key)
from utils.public import (insert_location, delete_terminal,
     record_add_action, get_terminal_type_by_tid, clear_data,
     update_terminal_info, subscription_lbmp, add_terminal, add_user) 

from helpers.queryhelper import QueryHelper
from helpers.smshelper import SMSHelper
from helpers.wspushhelper import WSPushHelper

from constants import EVENTER, GATEWAY, UWEB, SMS

from error import GWException
            
from handlers.basic import (append_gw_request, update_terminal_status, get_resend_flag)

def handle_new_login(t_info, address, connection, channel, exchange, gw_binding, db, redis):
    """Handle the login packet with version bigger than 2.2.0
    S1

    t_info:{'dev_id' // tid
            't_msisdn' // tmobile
            'u_msisdn' // umobile
            'imei' // sim's id 
            'imsi' // track's id 
            'dev_type' 
            'softversion' // version of terminal, like 2.3.0
            'timestamp'
            'psd' 
            'keys_num' 
            'sessionID' 
            'command'  
            'factory_name'  
           }

    flag(t_info['psd']):
      0 - boot_normally
      1 - active_terminal
      2 - assert_reboot 
      3 - network_uncovered 
      4 - server_no_response 
      5 - config_changed 
      6 - session_expired 
      7 - terminal_unactived 
      8 - package_send_fail 
      9 - simcard_error 
     10 - gprs_error 
     11 - mcu_timeout
     12 - reboot_by_sms
    100 - script_reload 

    workflow:
    if normal login:
       if sn and imsi exist, but msisdn and msisdn are empty: 
           send register sms again 
       normal login, check [SN,PHONE,IMSI,USER] is matching or not.
    else: #JH
       delete old bind relation of tid, and send message to old user.
       update new bind relation of tmobile, and send message to new user.

    login response packet:
    0 - success, then get a sessionID for terminal and record terminal's address
    1 - unregister, terminal login first.
    3 - illegal sim, a mismatch between [SN,PHONE,IMSI,USER] 
    6 - not whitelist

    """

    args = DotDict(success=GATEWAY.LOGIN_STATUS.SUCCESS,
                   sessionID='')
    tid = t_info.dev_id

    resend_key, resend_flag = get_resend_flag(redis, tid, t_info.timestamp, t_info.command) 

    sms = ''
    t_status = None
    #NOTE: new softversion, new meaning, 1: active; othter: normal login
    flag = t_info['psd'] 
    terminal = db.get("SELECT tid, group_id, mobile, imsi, owner_mobile, service_status,"
                      "   defend_status, mannual_status, icon_type, login_permit, "
                      "   alias, vibl, use_scene, push_status, speed_limit, stop_interval"
                      "  FROM T_TERMINAL_INFO"
                      "  WHERE mobile = %s LIMIT 1",
                      t_info['t_msisdn']) 

    #NOTE: normal login
    if flag != "1": # normal login
        #NOTE: no tmobile and ower_mobile 
        if (not t_info['t_msisdn']) and (not t_info['u_msisdn']):
            t = db.get("SELECT tid, group_id, mobile, imsi, owner_mobile, service_status"
                       "  FROM T_TERMINAL_INFO"
                       "  WHERE service_status=1"
                       "      AND tid = %s "
                       "      AND imsi = %s LIMIT 1",
                       t_info['dev_id'], t_info['imsi']) 
            if t: 
                args.success = GATEWAY.LOGIN_STATUS.ILLEGAL_SIM
                t_info['t_msisdn'] = t.mobile
                t_info['u_msisdn'] = t.owner_mobile
                register_sms = SMSCode.SMS_REGISTER % (t.owner_mobile, t.mobile)
                SMSHelper.send_to_terminal(t.mobile, register_sms)
                logging.info("[GW] A crash terminal tid:%s, imei:%s has no tmobile: %s, umobile:%s in login packet, so send %s again.",
                             t_info['dev_id'], t_info['imei'], t_info['t_msisdn'], t_info['u_msisdn'], register_sms)
            else:
                args.success = GATEWAY.LOGIN_STATUS.ILLEGAL_SIM
                logging.info("[GW] A crash terminal:%s login without umobile and tmobile, and there is no record in db.", t_info['dev_id'])
        else:
            #NOTE: no tmobile 
            if not t_info['t_msisdn']:
                # login first.
                tid_terminal = db.get("SELECT tid, mobile, owner_mobile, service_status"
                                      " FROM T_TERMINAL_INFO"
                                      " WHERE tid = %s LIMIT 1", t_info['dev_id'])
                args.success = GATEWAY.LOGIN_STATUS.ILLEGAL_SIM
                if tid_terminal:
                    #NOTE: mobile is not not JH, send caution to owner
                    sms_ = SMSCode.SMS_NOT_JH % tid_terminal.mobile 
                    SMSHelper.send(tid_terminal.owner_mobile, sms_)
                logging.warn("[GW] terminal: %s login at first time.",
                             t_info['dev_id'])
            #NOTE: tmobile is exist
            elif terminal:
                alias = QueryHelper.get_alias_by_tid(terminal['tid'], redis, db)
                if terminal['tid'] != t_info['dev_id']:
                    args.success = GATEWAY.LOGIN_STATUS.ILLEGAL_SIM
                    sms = SMSCode.SMS_TERMINAL_HK % alias 
                    logging.warn("[GW] Terminal changed dev, mobile: %s, old_tid: %s, new_tid: %s",
                                 t_info['t_msisdn'], terminal['tid'], t_info['dev_id'])
                elif terminal['imsi'] != t_info['imsi']:
                    args.success = GATEWAY.LOGIN_STATUS.ILLEGAL_SIM
                    sms = SMSCode.SMS_TERMINAL_HK % alias 
                    logging.warn("[GW] Terminal imsi is wrong, tid: %s, mobile: %s, old_imsi: %s, new_imsi: %s",
                                 t_info['dev_id'], t_info['t_msisdn'], terminal['imsi'], t_info['imsi'])
                elif terminal['owner_mobile'] != t_info['u_msisdn']:
                    register_sms = SMSCode.SMS_REGISTER % (terminal['owner_mobile'], terminal['mobile']) 
                    SMSHelper.send_to_terminal(terminal['mobile'], register_sms)
                    logging.warn("[GW] Terminal owner_mobile is wrong, tid: %s, old_owner_mobile: %s, new_owner_mobile: %s, send the regist sms: %s again",
                                 t_info['dev_id'], terminal['owner_mobile'], t_info['u_msisdn'], register_sms)
                elif terminal['service_status'] == UWEB.SERVICE_STATUS.TO_BE_UNBIND:
                    t_status = UWEB.SERVICE_STATUS.TO_BE_UNBIND
                    logging.warn("[GW] Terminal is unbinded. tid: %s, mobile: %s", 
                                 t_info["dev_id"], t_info['t_msisdn'])            
                else:
                    logging.info("[GW] Terminal normal login successfully. tid: %s, mobile: %s", 
                                 t_info['dev_id'], t_info['t_msisdn'])
            else:
                args.success = GATEWAY.LOGIN_STATUS.UNREGISTER
                logging.error("[GW] Terminal login failed, unregister. tid: %s, mobile: %s", 
                              t_info['dev_id'], t_info['t_msisdn'])
    #NOTE: JH
    else: # JH 
        logging.info("[GW] Terminal JH started. tid: %s, mobile: %s",
                     t_info['dev_id'], t_info['t_msisdn'])
        # 0. Initialize the valus keeps same as the default value in database.
        group_id = -1
        login_permit = 1 
        mannual_status = UWEB.DEFEND_STATUS.YES
        defend_status = UWEB.DEFEND_STATUS.YES
        icon_type = 0
        alias = ''
        push_status = 1
        vibl = 1
        use_scene = 3
        speed_limit = 120
        stop_interval = 0
        # send JH sms to terminal. default active time is one year.
        begintime = datetime.datetime.now() 
        endtime = begintime + relativedelta(years=1)

        # 1. check data validation
        logging.info("[GW] Checking terminal mobile: %s and owner mobile: %s, Terminal: %s",
                     t_info['t_msisdn'], t_info['u_msisdn'], t_info['dev_id'])
        if not (check_phone(t_info['u_msisdn']) and check_phone(t_info['t_msisdn'])):
            args.success = GATEWAY.LOGIN_STATUS.ILLEGAL_SIM
            lc = LoginRespComposer(args)
            request = DotDict(packet=lc.buf,
                              address=address,
                              dev_id=t_info['dev_id'])
            if t_info['u_msisdn']:
                # send JH failed caution to owner
                sms = SMSCode.SMS_JH_FAILED
                SMSHelper.send(t_info['u_msisdn'], sms)
            logging.error("[GW] Login failed! Invalid terminal mobile: %s or owner_mobile: %s, tid: %s",
                          t_info['t_msisdn'], t_info['u_msisdn'], t_info['dev_id'])

            append_gw_request(request, connection, channel, exchange, gw_binding)
        # 2. delete to_be_unbind terminal
        if terminal and terminal.service_status == UWEB.SERVICE_STATUS.TO_BE_UNBIND:
            logging.info("[GW] Delete terminal which is to_be_unbind. tid: %s, mobile: %s", 
                         terminal['tid'], terminal['mobile'])
            delete_terminal(terminal['tid'], db, redis)
            terminal = None

        # 3. add user info
        exist = db.get("SELECT id FROM T_USER"
                       "  WHERE mobile = %s",
                       t_info['u_msisdn'])

        #NOTE: Check ydcw or ajt
        ajt = QueryHelper.get_ajt_whitelist_by_mobile(t_info['t_msisdn'], db)
        if ajt:
           url_out = ConfHelper.UWEB_CONF.ajt_url_out
        else:
           url_out = ConfHelper.UWEB_CONF.url_out
        logging.info("[GW] Login url is: %s, tid: %s, mobile: %s ", 
                     url_out, t_info['dev_id'], t_info['t_msisdn'])

        if exist:
            logging.info("[GW] Owner already existed. tid: %s, mobile: %s", 
                         t_info['dev_id'], t_info['t_msisdn'])
            sms = SMSCode.SMS_USER_ADD_TERMINAL % (t_info['t_msisdn'],
                                                   url_out)
        else:
            # get a new psd for new user
            logging.info("[GW] Create new owner started. tid: %s, mobile: %s", t_info['dev_id'], t_info['t_msisdn'])
            psd = get_psd()
            user_info = dict(umobile=t_info['u_msisdn'],
                             password=psd, 
                             uname=t_info['u_msisdn'])
            add_user(user_info, db, redis)
            sms = SMSCode.SMS_JH_SUCCESS % (t_info['t_msisdn'],
                                            url_out,
                                            t_info['u_msisdn'],
                                            psd)

        # 4. JH existed tmobile
        is_refurbishment = False
        if terminal:
            if (terminal['tid'] == t_info['dev_id']) and \
               (terminal['imsi'] == t_info['imsi']) and \
               (terminal['owner_mobile'] == t_info['u_msisdn']):
                # 4.1 SCN: Refurbishment, the terminal-info has existed in platform. JH it again.
                is_refurbishment = True 
                # check the login packet whether is send again 
                if resend_flag:
                    sms = ''
                    logging.info("[GW] Recv resend packet, do not send sms. tid: %s, mobile: %s", 
                                 t_info['dev_id'], t_info['t_msisdn'])
                else:
                    sms = SMSCode.SMS_USER_ADD_TERMINAL % (t_info['t_msisdn'],
                                                           url_out)
                    logging.info("[GW] Terminal is refurbishment. tid: %s, mobile: %s", 
                                 t_info['dev_id'], t_info['t_msisdn'])
            else:     
                # 4.2 existed tmobile changed dev or corp terminal login first, get the old info(group_id, login_permit and so on) before change
                group_id = terminal.group_id
                login_permit = terminal.login_permit 
                mannual_status = terminal.mannual_status
                defend_status = terminal.defend_status
                icon_type = terminal.icon_type
                alias = terminal.alias
                vibl = terminal.vibl
                use_scene = terminal.use_scene
                push_status = terminal.push_status
                speed_limit = terminal.speed_limit
                stop_interval = terminal.stop_interval
                if terminal.tid == terminal.mobile:
                    # corp terminal login first, keep corp info
                    db.execute("UPDATE T_REGION_TERMINAL"
                               "  SET tid = %s"
                               "  WHERE tid = %s",
                               t_info['dev_id'], t_info['t_msisdn'])
                    logging.info("[GW] Corp terminal login first, tid: %s, mobile: %s.",
                                 t_info['dev_id'], t_info['t_msisdn'])
                elif terminal.tid != t_info['dev_id']:
                    logging.info("[GW] Terminal changed dev, mobile: %s, new_tid: %s, delete old_tid: %s.",
                                 t_info['t_msisdn'], t_info['dev_id'], terminal.tid)
                else:
                    # Refurbishment, change user
                    logging.info("[GW] Terminal change user, tid: %s, mobile: %s, new_owner_mobile: %s, old_owner_mobile: %s",
                                 t_info['dev_id'], t_info['t_msisdn'], t_info['u_msisdn'],
                                 terminal.owner_mobile)
                #NOTE: If terminal has exist, firt remove the terminal 
                logging.info("[GW] Terminal is deleted, tid: %s, mobile: %s.",
                             terminal['tid'], terminal['mobile']) 
                del_user = True
                if terminal.owner_mobile != t_info['u_msisdn']:
                    # send message to old user of dev_id
                    sms_ = SMSCode.SMS_DELETE_TERMINAL % terminal.mobile 
                    SMSHelper.send(terminal.owner_mobile, sms_)
                    if terminal.tid == t_info['dev_id']: 
                        # clear data belongs to the terminal 
                        clear_data(terminal.tid, db, redis)
                    logging.info("[GW] Send delete terminal message: %s to user: %s",
                                 sms_, terminal.owner_mobile)
                else:
                    del_user = False
                delete_terminal(terminal.tid, db, redis, del_user=del_user)

        #NOTE: Normal JH.
        if not is_refurbishment:
            # 5. delete existed tid
            tid_terminal = db.get("SELECT tid, mobile, owner_mobile, service_status"
                                  "  FROM T_TERMINAL_INFO"
                                  "  WHERE tid = %s LIMIT 1",
                                  t_info['dev_id'])
            if tid_terminal:
                logging.info("[GW] Terminal is deleted, tid: %s, mobile: %s.",
                             tid_terminal['tid'], tid_terminal['mobile']) 
                del_user = True
                if tid_terminal['owner_mobile'] != t_info['u_msisdn']:
                    if tid_terminal['service_status'] == UWEB.SERVICE_STATUS.TO_BE_UNBIND:
                        logging.info("[GW] Terminal is to_be_unbind, tid: %s, mobile: %s, delete it.",
                                     tid_terminal['tid'], tid_terminal['mobile']) 
                    else:
                        # send message to old user of dev_id
                        sms_ = SMSCode.SMS_DELETE_TERMINAL % tid_terminal['mobile'] 
                        SMSHelper.send(tid_terminal['owner_mobile'], sms_)
                        logging.info("[GW] Send delete terminal message: %s to user: %s",
                                     sms_, tid_terminal['owner_mobile'])
                        # user changed, must clear history data of dev_id
                        clear_data(tid_terminal['tid'], db, redis)
                else:
                    del_user = False
                delete_terminal(tid_terminal['tid'], db, redis, del_user=del_user)

            # 6 add terminal info
           
            # check use sence
            ttype = get_terminal_type_by_tid(t_info['dev_id'])
            logging.info("[GW] Terminal's type is %s. tid: %s, mobile: %s", 
                         ttype, t_info['dev_id'], t_info['t_msisdn']) 

            terminal_info = dict(tid=t_info['dev_id'],
                                 group_id=group_id,
                                 dev_type=t_info['dev_type'],
                                 tmobile=t_info['t_msisdn'],
                                 owner_mobile=t_info['u_msisdn'],
                                 imsi=t_info['imsi'],
                                 imei=t_info['imei'],
                                 factory_name=t_info['factory_name'],
                                 softversion=t_info['softversion'], 
                                 keys_num=t_info['keys_num'], 
                                 login=GATEWAY.TERMINAL_LOGIN.ONLINE,
                                 service_status=UWEB.SERVICE_STATUS.ON,
                                 mannual_status=mannual_status,
                                 push_status=push_status,
                                 icon_type=icon_type,
                                 begintime=int(time.mktime(begintime.timetuple())),
                                 endtime=4733481600,
                                 offline_time=int(time.mktime(begintime.timetuple())),
                                 cnum=alias,
                                 login_permit=login_permit,
                                 bt_mac=t_info['bt_mac'],
                                 bt_name=t_info['bt_name'],
                                 vibl=vibl,
                                 use_scene=use_scene,
                                 biz_type=UWEB.BIZ_TYPE.YDWS)
            add_terminal(terminal_info, db, redis)

            # record the add action, enterprise or individual
            corp = QueryHelper.get_corp_by_gid(group_id, db)
            bind_info = dict(tid=t_info['dev_id'],
                             tmobile=t_info['t_msisdn'],
                             umobile=t_info['u_msisdn'],
                             group_id=group_id,
                             cid=corp.get('cid', '') if corp else '',
                             add_time=int(time.time()))
            record_add_action(bind_info, db)
 
            logging.info("[GW] Terminal JH success! tid: %s, mobile: %s.",
                         t_info['dev_id'], t_info['t_msisdn'])
            # subscription LE for new sim
            thread.start_new_thread(subscription_lbmp, (t_info,)) 

    if args.success == GATEWAY.LOGIN_STATUS.SUCCESS:
        # get SessionID
        if resend_flag:
            logging.warn("[GW] Recv resend login packet and use old sessionID! packet: %s, tid: %s, mobile: %s.", 
                         t_info, t_info['dev_id'], t_info['t_msisdn']) 
            args.sessionID = QueryHelper.get_terminal_sessionID(t_info['dev_id'], redis)
            if not args.sessionID:
                args.sessionID = get_sessionID()
        else:
            #NOTE: generate a sessionid and keep it in redis.
            args.sessionID = get_sessionID()
            terminal_sessionID_key = get_terminal_sessionID_key(t_info['dev_id'])
            redis.setvalue(terminal_sessionID_key, args.sessionID)
            redis.setvalue(resend_key, True, GATEWAY.RESEND_EXPIRY)
        # record terminal address
        update_terminal_status(redis, t_info["dev_id"], address)
        #NOTE: When termianl is normal login, update some properties to platform.
        info = DotDict(login=GATEWAY.TERMINAL_LOGIN.ONLINE,
                       mobile=t_info['t_msisdn'],
                       keys_num=t_info['keys_num'],
                       softversion=t_info['softversion'],
                       login_time=int(time.time()),
                       dev_id=t_info["dev_id"],
                       bt_mac=t_info['bt_mac'],
                       bt_name=t_info['bt_name'],
                       dev_type=t_info['dev_type'])
        update_terminal_info(db, redis, info)
        logging.info("[GW] Terminal login success! tid: %s, mobile: %s",
                     t_info['dev_id'], t_info['t_msisdn'])

        #NOTE: wspush to cient
        if flag != "1": # normal login
            WSPushHelper.pushS4(t_info["dev_id"], db, redis)
        else: # JH 
            pass

    lc = LoginRespComposer(args)
    request = DotDict(packet=lc.buf,
                      address=address,
                      dev_id=t_info["dev_id"])
    append_gw_request(request, connection, channel, exchange, gw_binding)

    if sms and t_info['u_msisdn']:
        logging.info("[GW] Send sms to owner. mobile: %s, content: %s",
                    t_info['u_msisdn'], sms)
        SMSHelper.send(t_info['u_msisdn'], sms)

    if t_status == UWEB.SERVICE_STATUS.TO_BE_UNBIND:
        seq = str(int(time.time()*1000))[-4:]
        args_ = DotDict(seq=seq,
                        tid=t_info["dev_id"])
        ubc = UNBindComposer(args_)
        request = DotDict(packet=ubc.buf,
                          address=address,
                          dev_id=t_info["dev_id"])
        append_gw_request(request, connection, channel, exchange, gw_binding)
        logging.warn("[GW] Terminal is unbinded, tid: %s, send unbind packet.", t_info["dev_id"])            

def handle_old_login(t_info, address, connection, channel, exchange, gw_binding, db, redis):
    """
    S1
    Login response packet:

    0 - success, then get a sessionID for terminal and record terminal's address
    1 - illegal format of sim
    2 - expired, service stop or endtime < now
    3 - illegal sim, a mismatch between imsi and sim
    4 - psd wrong. HK
    5 - dev_id is empty
    6 - not whitelist
    """
    sms = None
    args = DotDict(success=GATEWAY.LOGIN_STATUS.SUCCESS,
                   sessionID='')
    dev_id = t_info['dev_id']

    resend_key, resend_flag = get_resend_flag(redis, dev_id, t_info.timestamp, t_info.command) 

    logging.info("[GW] Checking terminal mobile: %s and owner mobile: %s, Terminal: %s",
                 t_info['t_msisdn'], t_info['u_msisdn'], t_info['dev_id'])
    if not (check_phone(t_info['u_msisdn']) and check_phone(t_info['t_msisdn'])):
        args.success = GATEWAY.LOGIN_STATUS.ILLEGAL_SIM
        lc = LoginRespComposer(args)
        request = DotDict(packet=lc.buf,
                          address=address,
                          dev_id=t_info["dev_id"])
        append_gw_request(request, connection, channel, exchange, gw_binding)
        logging.error("[GW] Login failed! Invalid terminal mobile: %s or owner_mobile: %s, dev_id: %s",
                      t_info['t_msisdn'], t_info['u_msisdn'], t_info['dev_id'])
        return

    t_status = db.get("SELECT service_status"
                      "  FROM T_TERMINAL_INFO"
                      "  WHERE mobile = %s",
                      t_info['t_msisdn'])
    if t_status and t_status.service_status == GATEWAY.SERVICE_STATUS.OFF:
        args.success = GATEWAY.LOGIN_STATUS.EXPIRED
        lc = LoginRespComposer(args)
        request = DotDict(packet=lc.buf,
                          address=address,
                          dev_id=t_info["dev_id"])
        append_gw_request(request, connection, channel, exchange, gw_binding)
        logging.error("[GW] Login failed! terminal service expired! mobile: %s, dev_id: %s",
                      t_info['t_msisdn'], t_info['dev_id'])
        return


    logging.info("[GW] Checking imsi: %s and mobile: %s, Terminal: %s",
                 t_info['imsi'], t_info['t_msisdn'], t_info['dev_id'])
    tmobile = db.get("SELECT imsi FROM T_TERMINAL_INFO"
                     "  WHERE mobile = %s", t_info['t_msisdn'])
    if tmobile and tmobile.imsi and tmobile.imsi != t_info['imsi']:
        # check terminal and give a appropriate HK notification
        terminal = db.get("SELECT id FROM T_TERMINAL_INFO WHERE tid=%s", t_info['dev_id'])
        if terminal:
            alias = QueryHelper.get_alias_by_tid(t_info['dev_id'], redis, db)
        else: 
            alias = t_info['t_msisdn']
        args.success = GATEWAY.LOGIN_STATUS.ILLEGAL_SIM
        sms = SMSCode.SMS_TERMINAL_HK % alias 
        SMSHelper.send(t_info['u_msisdn'], sms)
        lc = LoginRespComposer(args)
        request = DotDict(packet=lc.buf,
                          address=address,
                          dev_id=t_info["dev_id"])
        append_gw_request(request, connection, channel, exchange, gw_binding)
        logging.error("[GW] Login failed! Illegal SIM: %s for Terminal: %s",
                      t_info['t_msisdn'], t_info['dev_id'])
        return

    terminal = db.get("SELECT id, mobile, owner_mobile, service_status"
                      "  FROM T_TERMINAL_INFO"
                      "  WHERE tid = %s", t_info['dev_id'])
    if terminal:
        if terminal.mobile != t_info['t_msisdn']:
            logging.info("[GW] Terminal: %s changed mobile, old mobile: %s, new mobile: %s",
                         t_info['dev_id'], terminal.mobile,
                         t_info['t_msisdn'])
            if (terminal.owner_mobile == t_info['u_msisdn'] or
                terminal.service_status == UWEB.SERVICE_STATUS.TO_BE_UNBIND):
                # delete old terminal!
                logging.info("[GW] Delete old tid bind relation. tid: %s, owner_mobile: %s, service_status: %s",
                             t_info['dev_id'], t_info['u_msisdn'],
                             terminal.service_status)
                delete_terminal(t_info['dev_id'], db, redis, del_user=False)
                exist = db.get("SELECT tid, owner_mobile, service_status FROM T_TERMINAL_INFO"
                               "  WHERE mobile = %s LIMIT 1",
                               t_info['t_msisdn'])
                if exist:
                    # cannot send unbind packet to dev_id
                    t_status = None
                    logging.info("[GW] Delete old tmobile bind relation. tid: %s, mobile: %s",
                                 exist.tid, t_info['t_msisdn'])
                    delete_terminal(exist.tid, db, redis, del_user=False)
                    if exist.service_status == UWEB.SERVICE_STATUS.TO_BE_UNBIND:
                        logging.info("[GW] Terminal: %s of %s is to_be_unbind, delete it.",
                                     exist.tid, t_info['t_msisdn'])
                    elif exist.owner_mobile != t_info['u_msisdn']:
                        sms = SMSCode.SMS_DELETE_TERMINAL % t_info['t_msisdn']
                        SMSHelper.send(exist.owner_mobile, sms)
                terminal = None
            else:
                args.success = GATEWAY.LOGIN_STATUS.ILLEGAL_SIM
                sms = SMSCode.SMS_TID_EXIST % t_info['dev_id']
                SMSHelper.send(t_info['u_msisdn'], sms)
                lc = LoginRespComposer(args)
                request = DotDict(packet=lc.buf,
                                  address=address,
                                  dev_id=t_info["dev_id"])
                append_gw_request(request, connection, channel, exchange, gw_binding)
                logging.error("[GW] Login failed! Terminal: %s already bound by %s, new mobile: %s",
                              t_info['dev_id'], terminal.mobile, t_info['t_msisdn'])
                return

    #NOTE: Check ydcw or ajt 
    ajt = QueryHelper.get_ajt_whitelist_by_mobile(t_info['t_msisdn'], db) 
    if ajt: 
        url_out = ConfHelper.UWEB_CONF.ajt_url_out 
    else: 
        url_out = ConfHelper.UWEB_CONF.url_out 
    logging.info("[GW] Terminal: %s, login url is: %s", t_info['t_msisdn'], url_out)

    if t_info['psd']:
        # check terminal exist or not when HK
        if not terminal:
            args.success = GATEWAY.LOGIN_STATUS.UNREGISTER
            sms = SMSCode.SMS_TID_NOT_EXIST
            SMSHelper.send(t_info['u_msisdn'], sms)
            lc = LoginRespComposer(args)
            request = DotDict(packet=lc.buf,
                              address=address,
                              dev_id=t_info["dev_id"])
            append_gw_request(request, connection, channel, exchange, gw_binding)
            logging.error("[GW] Login failed! Terminal %s execute HK, but tid is not exist",
                          t_info['dev_id'])
            return
        # HK, change terminal mobile or owner mobile
        logging.info("[GW] Checking password. Terminal: %s",
                     t_info['dev_id'])
        owner = db.get("SELECT id FROM T_USER"
                       "  WHERE mobile = %s"
                       "    AND password = password(%s)",
                       terminal.owner_mobile, t_info['psd'])
        if not owner:
            # psd wrong
            sms = SMSCode.SMS_PSD_WRONG
            args.success = GATEWAY.LOGIN_STATUS.PSD_WRONG
            logging.error("[GW] Login failed! Password invalid. Terminal: %s",
                          t_info['dev_id'])
        else:
            if terminal:
                if terminal.mobile != t_info['t_msisdn']:
                    # terminal HK
                    logging.info("[GW] Terminal: %s HK started.", t_info['dev_id'])
                    # unbind old tmobile
                    old_bind = db.get("SELECT id, tid FROM T_TERMINAL_INFO"
                                      "  WHERE mobile = %s"
                                      "    AND id != %s",
                                      t_info['t_msisdn'], terminal.id)
                    if old_bind:
                        # clear db
                        db.execute("DELETE FROM T_TERMINAL_INFO"
                                   "  WHERE id = %s", 
                                   old_bind.id) 
                        # clear redis
                        sessionID_key = get_terminal_sessionID_key(old_bind.tid)
                        address_key = get_terminal_address_key(old_bind.tid)
                        info_key = get_terminal_info_key(old_bind.tid)
                        lq_sms_key = get_lq_sms_key(old_bind.tid)
                        lq_interval_key = get_lq_interval_key(old_bind.tid)
                        keys = [sessionID_key, address_key, info_key, lq_sms_key, lq_interval_key]
                        redis.delete(*keys)
                        logging.info("[GW] Delete old bind Terminal: %s, SIM: %s",
                                     t_info['dev_id'], t_info['t_msisdn'])

                    # update new tmobile
                    db.execute("UPDATE T_TERMINAL_INFO"
                               "  SET mobile = %s,"
                               "      imsi = %s"
                               "  WHERE id = %s",
                               t_info['t_msisdn'],
                               t_info['imsi'], terminal.id)
                    # clear redis
                    sessionID_key = get_terminal_sessionID_key(t_info['dev_id'])
                    address_key = get_terminal_address_key(t_info['dev_id'])
                    info_key = get_terminal_info_key(t_info['dev_id'])
                    lq_sms_key = get_lq_sms_key(t_info['dev_id'])
                    lq_interval_key = get_lq_interval_key(t_info['dev_id'])
                    keys = [sessionID_key, address_key, info_key, lq_sms_key, lq_interval_key]
                    redis.delete(*keys)
                    # HK sms
                    sms = SMSCode.SMS_TERMINAL_HK_SUCCESS % (terminal.mobile, t_info['t_msisdn'])
                    # subscription LE for new sim
                    thread.start_new_thread(subscription_lbmp, (t_info,)) 
                    logging.info("[GW] Terminal: %s HK success!", t_info['dev_id'])

                if terminal.owner_mobile != t_info['u_msisdn']:
                    logging.info("[GW] Owner HK started. Terminal: %s", t_info['dev_id'])
                    # owner HK
                    user = db.get("SELECT id FROM T_USER"
                                  "  WHERE mobile = %s",
                                  t_info['u_msisdn'])
                    if user:
                        logging.info("[GW] Owner already existed. Terminal: %s", t_info['dev_id'])
                        sms = SMSCode.SMS_USER_ADD_TERMINAL % (t_info['t_msisdn'],
                                                               url_out) 
                    else:
                        logging.info("[GW] Create new owner started. Terminal: %s", t_info['dev_id'])
                        psd = get_psd()
                        user_info = dict(umobile=t_info['u_msisdn'],
                                         password=psd)
                        add_user(user_info, db, redis)
                        sms = SMSCode.SMS_USER_HK_SUCCESS % (t_info['u_msisdn'],
                                                             url_out,
                                                             t_info['u_msisdn'],
                                                             psd)
                    db.execute("UPDATE T_TERMINAL_INFO"
                               "  SET owner_mobile = %s"
                               "  WHERE id = %s",
                               t_info['u_msisdn'], terminal.id)
                    logging.info("[GW] Owner of %s HK success!", t_info['dev_id'])
            else:
                logging.error("[GW] What happened? Cannot find old terminal by dev_id: %s",
                              t_info['dev_id']) 
    else:
        # login or JH
        if terminal:
            # login
            logging.info("[GW] Terminal: %s Normal login started!",
                         t_info['dev_id']) 
        else:
            # SMS JH or admin JH or change new dev JH
            logging.info("[GW] Terminal: %s, mobile: %s JH started.",
                         t_info['dev_id'], t_info['t_msisdn'])
            exist = db.get("SELECT id FROM T_USER"
                           "  WHERE mobile = %s",
                           t_info['u_msisdn'])
            if exist:
                logging.info("[GW] Owner already existed. Terminal: %s", t_info['dev_id'])
                sms = SMSCode.SMS_USER_ADD_TERMINAL % (t_info['t_msisdn'],
                                                       url_out)
            else:
                # get a new psd for new user
                logging.info("[GW] Create new owner started. Terminal: %s", t_info['dev_id'])
                psd = get_psd()

                user_info = dict(umobile=t_info['u_msisdn'],
                                 password=psd,
                                 uname=t_info['u_msisdn'])
                add_user(user_info, db, redis)

                sms = SMSCode.SMS_JH_SUCCESS % (t_info['t_msisdn'],
                                                url_out,
                                                t_info['u_msisdn'],
                                                psd)

            admin_terminal = db.get("SELECT id, tid FROM T_TERMINAL_INFO"
                                    "  WHERE tid = %s",
                                    t_info['t_msisdn'])
            if admin_terminal:
                # admin JH
                db.execute("UPDATE T_TERMINAL_INFO"
                           "  SET tid = %s,"
                           "      dev_type = %s,"
                           "      owner_mobile = %s,"
                           "      imsi = %s,"
                           "      imei = %s,"
                           "      factory_name = %s,"
                           "      keys_num = %s,"
                           "      softversion = %s"
                           "  WHERE id = %s",
                           t_info['dev_id'],
                           t_info['dev_type'],
                           t_info['u_msisdn'],
                           t_info['imsi'],
                           t_info['imei'],
                           t_info['factory_name'],
                           t_info['keys_num'],
                           t_info['softversion'],
                           admin_terminal.id)
                db.execute("UPDATE T_CAR SET tid = %s"
                           "  WHERE tid = %s",
                           t_info['dev_id'], t_info['t_msisdn'])
                logging.info("[GW] Terminal %s by ADMIN JH success!", t_info['dev_id'])
            else:
                exist_terminal = db.get("SELECT id, tid FROM T_TERMINAL_INFO"
                                        "  WHERE mobile = %s",
                                        t_info['t_msisdn'])
                if exist_terminal:
                    # unbind old tmobile
                    db.execute("DELETE FROM T_TERMINAL_INFO"
                               "  WHERE id = %s",
                               exist_terminal.id)
                    # clear redis
                    sessionID_key = get_terminal_sessionID_key(exist_terminal.tid)
                    address_key = get_terminal_address_key(exist_terminal.tid)
                    info_key = get_terminal_info_key(exist_terminal.tid)
                    lq_sms_key = get_lq_sms_key(exist_terminal.tid)
                    lq_interval_key = get_lq_interval_key(exist_terminal.tid)
                    keys = [sessionID_key, address_key, info_key, lq_sms_key, lq_interval_key]
                    redis.delete(*keys)
                    logging.info("[GW] Terminal %s change dev, old dev: %s!",
                                 t_info['dev_id'], exist_terminal.tid)

                # send JH sms to terminal. default active time
                # is one year.
                begintime = datetime.datetime.now() 
                endtime = begintime + relativedelta(years=1)

                terminal_info = dict(tid=t_info['dev_id'],
                                     dev_type=t_info['dev_type'],
                                     tmobile=t_info['t_msisdn'],
                                     owner_mobile=t_info['u_msisdn'],
                                     imsi=t_info['imsi'],
                                     imei=t_info['imei'],
                                     factory_name=t_info['factory_name'],
                                     softversion=t_info['softversion'],
                                     keys_num=t_info['keys_num'],
                                     login=GATEWAY.TERMINAL_LOGIN.ONLINE,
                                     service_status=UWEB.SERVICE_STATUS.ON,
                                     group_id=-1,
                                     mannual_status=UWEB.DEFEND_STATUS.YES,
                                     begintime=int(time.mktime(begintime.timetuple())),
                                     endtime=4733481600,
                                     offline_time=int(time.mktime(begintime.timetuple())),
                                     biz_type=UWEB.BIZ_TYPE.YDWS)
                add_terminal(terminal_info, db, redis)

                # record the add action, enterprise or individual
                bind_info = dict(tid=t_info['dev_id'],
                                 tmobile=t_info['t_msisdn'],
                                 umobile=t_info['u_msisdn'],
                                 group_id=-1,
                                 cid='',
                                 add_time=int(time.time()))
                record_add_action(bind_info, db)

                logging.info("[GW] Terminal %s by SMS JH success!", t_info['dev_id'])

            # subscription LE for new sim
            thread.start_new_thread(subscription_lbmp, (t_info,)) 

    if args.success == GATEWAY.LOGIN_STATUS.SUCCESS:
        # get SessionID
        if resend_flag:
            args.sessionID = QueryHelper.get_terminal_sessionID(t_info['dev_id'], redis)
            logging.warn("[GW] Recv resend login packet: %s and use old sessionID: %s!", t_info, args.sessionID) 
            if not args.sessionID:
                args.sessionID = get_sessionID()
        else:
            args.sessionID = get_sessionID()
            terminal_sessionID_key = get_terminal_sessionID_key(t_info['dev_id'])
            redis.setvalue(terminal_sessionID_key, args.sessionID)
            redis.setvalue(resend_key, True, GATEWAY.RESEND_EXPIRY)
        # record terminal address
        update_terminal_status(redis, t_info["dev_id"], address)
        # set login
        info = DotDict(login=GATEWAY.TERMINAL_LOGIN.ONLINE,
                       mobile=t_info['t_msisdn'],
                       keys_num=t_info['keys_num'],
                       login_time=int(time.time()),
                       dev_id=t_info["dev_id"])
        update_terminal_info(db, redis, info)
        logging.info("[GW] Terminal %s login success! SIM: %s",
                     t_info['dev_id'], t_info['t_msisdn'])

        #NOTE: wspush to cient
        if flag != "1": # normal login
            WSPushHelper.pushS4(t_info["dev_id"], db, redis)
        else: # JH 
            pass

    lc = LoginRespComposer(args)
    request = DotDict(packet=lc.buf,
                      address=address,
                      dev_id=t_info["dev_id"])
    append_gw_request(request, connection, channel, exchange, gw_binding)
            
    if sms and t_info['u_msisdn']:
        SMSHelper.send(t_info['u_msisdn'], sms)

    # unbind terminal of to_be_unbind
    if t_status and t_status.service_status == UWEB.SERVICE_STATUS.TO_BE_UNBIND:
        logging.info("[GW] Terminal: %s is unbinded, send unbind packet.", t_info["dev_id"])            
        seq = str(int(time.time()*1000))[-4:]
        args = DotDict(seq=seq,
                       tid=t_info["dev_id"])
        ubc = UNBindComposer(args)
        request = DotDict(packet=ubc.buf,
                          address=address,
                          dev_id=t_info["dev_id"])
        append_gw_request(request, connection, channel, exchange, gw_binding)
