# -*- coding: utf-8 -*-

import logging

from clw.packet.parser.heartbeat import HeartbeatParser 
from clw.packet.composer.heartbeat import HeartbeatRespComposer

from helpers.queryhelper import QueryHelper

from error import GWException
from utils.dotdict import DotDict
from utils.public import update_terminal_info
            
from constants import EVENTER, GATEWAY, UWEB, SMS

from utils.misc import get_acc_status_info_key

from handlers.basic import append_gw_request, update_terminal_status

def handle_heartbeat(info, address, connection, channel, exchange, gw_binding,db, redis):
    """
    S2
    heartbeat packet

    0: success, then record new terminal's address
    1: invalid SessionID 
    3: acc_status is changed 
    """
    try:
        head = info.head
        body = info.body
        dev_id = head.dev_id
        args = DotDict(success=GATEWAY.RESPONSE_STATUS.SUCCESS)
        old_softversion = False # if version < 2.4.0, true; else false.
        sessionID = QueryHelper.get_terminal_sessionID(dev_id, redis)

        if sessionID != head.sessionID:
            args.success = GATEWAY.RESPONSE_STATUS.INVALID_SESSIONID 
        else:
            hp = HeartbeatParser(body, head)
            heartbeat_info = hp.ret 
            is_sleep = False
            if heartbeat_info['sleep_status'] == '0':
                heartbeat_info['login'] = GATEWAY.TERMINAL_LOGIN.SLEEP
                is_sleep = True
            elif heartbeat_info['sleep_status'] == '1':
                heartbeat_info['login'] = GATEWAY.TERMINAL_LOGIN.ONLINE
                is_sleep = False
            elif heartbeat_info['sleep_status'] == '2': # query mode
                acc_status_info_key = get_acc_status_info_key(dev_id)
                acc_status_info = redis.getvalue(acc_status_info_key)
                if acc_status_info and int(acc_status_info['op_status']) == 0:  
                    args.timestamp = acc_status_info['timestamp']
                    args.op_type = acc_status_info['op_type']
                    # modify t2_status in acc_status_info
                    acc_status_info['t2_status'] = 1 # T2 query occurs 
                    redis.setvalue(acc_status_info_key, acc_status_info, UWEB.ACC_STATUS_EXPIRY)
                else: # if acc_status_info['op_status'] is 1, or no acc_status_info, set op_type is 2
                    args.timestamp = '' 
                    args.op_type = 2 # wait 


            else: #NOTE: it should never occur
                logging.error("[GW] Recv wrong sleep status: %s", heartbeat_info)
            del heartbeat_info['sleep_status']


            update_terminal_status(redis, head.dev_id, address, is_sleep)
            update_terminal_info(db, redis, heartbeat_info)

        if args['success'] == GATEWAY.RESPONSE_STATUS.SUCCESS:
            acc_status_info_key = get_acc_status_info_key(dev_id)
            acc_status_info = redis.getvalue(acc_status_info_key)
            if acc_status_info and (not acc_status_info['t2_status']): # T2(query) is need
                args['success'] = 3 # acc_status is changed
                logging.info("[GW] ACC_status is changed, dev_id: %s, acc_status_info: %s", 
                             dev_id, acc_status_info)

            #NOTE: check the version. 
            # if version is less than 2.4.0(not include 2.4.0), only has  success in args
            softversion = heartbeat_info['softversion']
            item = softversion.split(".")
            if int(item[0]) > 2:
                pass
            else: # A.B.C  A <= 2
                if int(item[1]) < 4: # A.B.C  B <= 4 
                    old_softversion = True
                else:
                    pass

        if old_softversion:
            logging.info("[GW] Old softversion(<2.4.0): %s, only success is provided in S2",
                         softversion)
            args = dict(success=args['success'])
        
        hc = HeartbeatRespComposer(args)
        request = DotDict(packet=hc.buf,
                          address=address,
                          dev_id=dev_id)
        append_gw_request(request, connection, channel, exchange, gw_binding)
    except:
        logging.exception("[GW] Hand heartbeat failed.")
        GWException().notify()
