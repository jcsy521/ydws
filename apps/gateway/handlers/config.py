# -*- coding: utf-8 -*-

import logging
import time

from clw.packet.parser.config import ConfigParser
from clw.packet.composer.config import ConfigRespComposer

from utils.dotdict import DotDict

from utils.misc import (get_resend_key, get_terminal_sessionID_key,
get_acc_status_info_key)

from helpers.queryhelper import QueryHelper
from helpers.smshelper import SMSHelper
from helpers.wspushhelper import WSPushHelper

from constants import EVENTER, GATEWAY, UWEB, SMS

from error import GWException
            
from handlers.basic import append_gw_request, update_terminal_status

def handle_config(info, address, connection, channel, exchange, gw_binding, db, redis):
    """
    S17
    Config packet

    0: success, then record new terminal's address
    1: invalid SessionID 
    """
    try:
        head = info.head
        body = info.body
        dev_id = head.dev_id
        args = DotDict(success=GATEWAY.RESPONSE_STATUS.SUCCESS,
                       domain="",
                       freq="",
                       trace="",
                       static_val="",
                       move_val="",
                       trace_para="",
                       vibl="",
                       use_scene="",
                       stop_interval="",
                       test="",
                       gps_enhanced="")
        sessionID = QueryHelper.get_terminal_sessionID(head.dev_id, redis)
        if sessionID != head.sessionID:
            args.success = GATEWAY.RESPONSE_STATUS.INVALID_SESSIONID 
        else:
            update_terminal_status(redis, head.dev_id, address)
            #TODO:
            terminal = db.get("SELECT track, freq, trace, mannual_status,"
                              "       trace_para, vibl, domain,"
                              "       use_scene, stop_interval, test, gps_enhanced"
                              "  FROM T_TERMINAL_INFO"
                              "  WHERE tid = %s", head.dev_id)
            args.domain = terminal.domain
            args.freq = terminal.freq
            args.trace = terminal.trace
            args.use_scene = terminal.use_scene
            args.stop_interval = terminal.stop_interval
            args.test = terminal.test
            args.gps_enhanced = terminal.gps_enhanced
            if terminal.track == 1: # turn on track
                args.trace_para = "60:1"
            else:
                args.trace_para = terminal.trace_para
            args.vibl = terminal.vibl

            #NOTE: get move_val and static_val according to mannual_status
            if int(terminal.mannual_status) != UWEB.DEFEND_STATUS.YES: # 撤防，智能设防
                move_val = 0
                static_val = 180 
            else: # 强力设防
                move_val = 60
                static_val = 0 
            args.move_val = move_val
            args.static_val = static_val 

        if args['success'] == GATEWAY.RESPONSE_STATUS.SUCCESS: 
            acc_status_info_key = get_acc_status_info_key(dev_id) 
            acc_status_info = redis.getvalue(acc_status_info_key) 
            if acc_status_info and (not acc_status_info['t2_status']): # T2(query) is need
                args['success'] = 3 # acc_status is changed 
                logging.info("[GW] ACC_status is changed, dev_id: %s, acc_status_info: %s", 
                             dev_id, acc_status_info)

        hc = ConfigRespComposer(args)
        request = DotDict(packet=hc.buf,
                          address=address,
                          dev_id=dev_id)
        append_gw_request(request, connection, channel, exchange, gw_binding)
    except:
        logging.exception("[GW] Hand query config exception.")
        raise GWException

