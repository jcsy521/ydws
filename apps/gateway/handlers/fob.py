# -*- coding: utf-8 -*-

import logging

from clw.packet.parser.fobinfo import FobInfoParser
from clw.packet.composer.fobinfo import FobInfoRespComposer

from helpers.queryhelper import QueryHelper

from error import GWException
from utils.dotdict import DotDict
from constants import EVENTER, GATEWAY, UWEB, SMS

from utils.misc import get_acc_status_info_key

from utils.public import update_terminal_info, update_fob_info
            
from handlers.basic import append_gw_request, get_resend_flag

def handle_fob_info(info, address, connection, channel, exchange, gw_binding, db, redis):
    """
    S19 
    NOTE: deprecated 

    fob info packet: add or remove fob
    0: success, then record new terminal's address
    1: invalid SessionID
    """
    try:
        head = info.head
        body = info.body
        dev_id = head.dev_id
        args = DotDict(success=GATEWAY.RESPONSE_STATUS.SUCCESS)
        sessionID = QueryHelper.get_terminal_sessionID(dev_id, redis)
        if sessionID != head.sessionID:
            args.success = GATEWAY.RESPONSE_STATUS.INVALID_SESSIONID 
        else:
            fp = FobInfoParser(body, head)
            fobinfo = fp.ret
            update_terminal_status(redis, head.dev_id, address)
            update_fob_info(db, redis, fobinfo)

        fc = FobInfoRespComposer(args)
        request = DotDict(packet=fc.buf,
                          address=address,
                          dev_id=dev_id)
        append_gw_request(request, connection, channel, exchange, gw_binding)
    except:
        logging.exception("[GW] Handle fob info report exception.")
        GWException().notify()

def handle_fob_status(info, address, connection, channel, exchange, gw_binding, db, redis):
    """
    S22 
    NOTE: deprecated 
    fob status packet: 0-no fob near, 1-have fob near
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
        if sessionID != head.sessionID:
            args.success = GATEWAY.RESPONSE_STATUS.INVALID_SESSIONID 
        else:
            if resend_flag:
                logging.warn("[GW] Recv resend packet, head: %s, body: %s and drop it!",
                             info.head, info.body)
            else: 
                redis.setvalue(resend_key, True, GATEWAY.RESEND_EXPIRY)
                hp = AsyncParser(body, head)
                fob_info = hp.ret 
                info = DotDict(fob_status=fob_info['fob_status'],
                               dev_id=fob_info['dev_id'])
                update_terminal_info(db, redis, fob_info)
            update_terminal_status(redis, head.dev_id, address)

        hc = AsyncRespComposer(args)
        request = DotDict(packet=hc.buf,
                          address=address,
                          dev_id=dev_id)
        append_gw_request(request, connection, channel, exchange, gw_binding)
    except:
        logging.exception("[GW] Handle fob status report exception.")
        GWException().notify()
