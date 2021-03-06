# -*- coding: utf-8 -*-

import logging

from clw.packet.composer.config import ConfigRespComposer

from utils.dotdict import DotDict

from utils.misc import get_acc_status_info_key

from helpers.queryhelper import QueryHelper

from constants import GATEWAY, UWEB

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
                       gps_enhanced="",
                       tracking_interval="")
        sessionID = QueryHelper.get_terminal_sessionID(head.dev_id, redis)
        if sessionID != head.sessionID:
            args.success = GATEWAY.RESPONSE_STATUS.INVALID_SESSIONID 
        else:
            update_terminal_status(redis, head.dev_id, address)
            #TODO:
            terminal = db.get("SELECT track, freq, trace, mannual_status,"
                              "       trace_para, vibl, domain,"
                              "       use_scene, stop_interval, test,"
                              "       gps_enhanced, tracking_interval"
                              "  FROM T_TERMINAL_INFO"
                              "  WHERE tid = %s", head.dev_id)
            args.domain = terminal.domain
            args.freq = terminal.freq
            args.trace = terminal.trace
            args.use_scene = terminal.use_scene
            args.stop_interval = terminal.stop_interval
            args.test = terminal.test
            args.gps_enhanced = terminal.gps_enhanced
            args.tracking_interval = terminal.tracking_interval
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

        #NOTE: check the version.
        # if version is after 2.4, add tracking-interval in S17
        softversion = head['softversion']
        item = softversion.split(".")
        old_softversion = False

        if int(item[0]) < 2: # 1.x.x
            old_softversion = True
        elif int(item[0]) == 2: # 2.x.x
            if int(item[1]) < 4: # 2.3.x
                old_softversion = True
            else: # 2.4.x
                old_softversion = False
        else: # 3.x
            old_softversion = False
        if old_softversion:
             del args['tracking_interval']

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
        GWException().notify()
