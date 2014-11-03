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
from mixin.login import handle_new_login, handle_old_login

def handle_login(info, address, connection, channel, exchange, gw_binding, db, redis):
    """
    S1
    Handle the login packet.

    workflow:
    1: check packet
    if not dev_id:
        send packt to terminal, illegal_devid
    if mobile is not whitelist: 
        send sms to owner, mobile is not whitelist
        
    if version is bigger than 2.2.0:
        handle_new_login
    else:
        handle_old_login
    """
    try:
        args = DotDict(success=GATEWAY.LOGIN_STATUS.SUCCESS,
                       sessionID='')

        if len(info.body) == 7:
            info.body.append("")
            info.body.append("")
            logging.info("[GW] old version is compatible, append bt_name, bt_mac")

        lp = LoginParser(info.body, info.head)
        t_info = lp.ret
        if not t_info['dev_id']:
            args.success = GATEWAY.LOGIN_STATUS.ILLEGAL_DEVID
            lc = LoginRespComposer(args)
            request = DotDict(packet=lc.buf,
                              address=address,
                              dev_id=t_info['dev_id'])
            append_gw_request(request, connection, channel, exchange, gw_binding)
            logging.error("[GW] Login failed! Invalid terminal dev_id: %s", t_info['dev_id'])

        if t_info['t_msisdn']:
            logging.info("[GW] Checking whitelist, terminal mobile: %s, Terminal: %s",
                         t_info['t_msisdn'], t_info['dev_id'])
            if not check_zs_phone(t_info['t_msisdn'], db):
                args.success = GATEWAY.LOGIN_STATUS.NOT_WHITELIST 
                lc = LoginRespComposer(args)
                request = DotDict(packet=lc.buf,
                                  address=address,
                                  dev_id=t_info['dev_id'])
                sms = SMSCode.SMS_MOBILE_NOT_WHITELIST % t_info['t_msisdn']
                SMSHelper.send(t_info['u_msisdn'], sms)
                logging.error("[GW] Login failed! terminal mobile: %s not whitelist, dev_id: %s",
                              t_info['t_msisdn'], t_info['dev_id'])
                append_gw_request(request, connection, channel, exchange, gw_binding)

        #NOTE: check the version. 
        # if version is after 2.2.0, go to handle_new_login; else go to handle_old_login
        softversion = t_info['softversion']
        item = softversion.split(".")
        new_softversion = True

        if int(item[0]) > 2:
            new_softversion = True
        elif int(item[0]) == 2:
            if int(item[1]) < 2:
                new_softversion = False 
            else:
                new_softversion = True 
        else:
            new_softversion = False

        if new_softversion: 
            # after v2.2.0
            logging.info("[GW] New softversion(>=2.2.0): %s, go to new login handler...",
                         softversion)
            handle_new_login(t_info, address, connection, channel, exchange, gw_binding, db, redis)
        else:
            # before v2.2.0
            logging.info("[GW] Old softversion(<2.2.0): %s, go to old login handler...",
                         softversion)
            handle_old_login(t_info, address, connection, channel, exchange, gw_binding, db, redis)
        # check use sence
        ttype = get_terminal_type_by_tid(t_info['dev_id'])
        logging.info("[GW] Terminal %s 's type  is %s", t_info['dev_id'], ttype)

    except:
        logging.exception("[GW] Handle login exception.")
        raise GWException

