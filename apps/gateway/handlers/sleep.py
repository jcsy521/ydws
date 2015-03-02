# -*- coding: utf-8 -*-

import logging

from clw.packet.parser.async import AsyncParser
from clw.packet.composer.async import AsyncRespComposer

from helpers.queryhelper import QueryHelper

from error import GWException
from utils.dotdict import DotDict
from utils.public import update_terminal_info
            
from constants import GATEWAY

from utils.misc import get_acc_status_info_key
            
from handlers.basic import (append_gw_request, update_terminal_status, get_resend_flag)


def handle_sleep(info, address, connection, channel, exchange, gw_binding, db, redis):
    """
    S21
    sleep status packet: 0-sleep, 1-LQ
    0: success, then record new terminal's address
    1: invalid SessionID
    """
    try:
        head = info.head
        body = info.body
        dev_id = head.dev_id

        resend_key, resend_flag = get_resend_flag(redis, dev_id, head.timestamp, head.command) 

        args = DotDict(success=GATEWAY.RESPONSE_STATUS.SUCCESS,
                       command=head.command)
        sessionID = QueryHelper.get_terminal_sessionID(dev_id, redis)
        is_sleep = False
        if sessionID != head.sessionID:
            args.success = GATEWAY.RESPONSE_STATUS.INVALID_SESSIONID 
        else:
            if resend_flag:
                logging.warn("[GW] Recv resend packet, head: %s, body: %s and drop it!",
                             info.head, info.body)
            else: 
                redis.setvalue(resend_key, True, GATEWAY.RESEND_EXPIRY)
                hp = AsyncParser(body, head)
                sleep_info = hp.ret 
                if sleep_info['sleep_status'] == '0':
                    sleep_info['login'] = GATEWAY.TERMINAL_LOGIN.SLEEP
                    #self.send_lq_sms(head.dev_id)
                    #logging.info("[GW] Recv sleep packet, LQ it: %s", head.dev_id)
                    is_sleep = True
                elif sleep_info['sleep_status'] == '1':
                    sleep_info['login'] = GATEWAY.TERMINAL_LOGIN.ONLINE
                else:
                    logging.info("[GW] Recv wrong sleep status: %s", sleep_info)
                del sleep_info['sleep_status']
                update_terminal_info(db, redis, sleep_info)

            update_terminal_status(redis, dev_id, address, is_sleep)

        if args['success'] == GATEWAY.RESPONSE_STATUS.SUCCESS: 
            acc_status_info_key = get_acc_status_info_key(dev_id) 
            acc_status_info = redis.getvalue(acc_status_info_key) 
            if acc_status_info and (not acc_status_info['t2_status']): # T2(query) is need
                args['success'] = 3 # acc_status is changed 
                logging.info("[GW] ACC_status is changed, dev_id: %s, acc_status_info: %s", 
                             dev_id, acc_status_info)

        hc = AsyncRespComposer(args)
        request = DotDict(packet=hc.buf,
                          address=address,
                          dev_id=dev_id)
        append_gw_request(request, connection, channel, exchange, gw_binding)
    except:
        logging.exception("[GW] Handle sleep status report exception.")
        GWException().notify()
