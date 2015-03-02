# -*- coding: utf-8 -*-

import logging

from clw.packet.parser.async import AsyncParser
from clw.packet.composer.async import AsyncRespComposer


from error import GWException
from utils.dotdict import DotDict
from utils.public import delete_terminal_new, clear_data
            
from constants import GATEWAY

from handlers.basic import append_gw_request

def handle_unbind_status(info, address, connection, channel, exchange, gw_binding, db, redis):
    """
    S25
    Unbind status report packet

    0: success, then record new terminal's address
    1: invalid SessionID 
    """
    request = None
    try:
        head = info.head
        body = info.body
        dev_id = head.dev_id
        # before v2.2.0
        if len(body) == 0:
            body.append("0")

        args = DotDict(success=GATEWAY.RESPONSE_STATUS.SUCCESS,
                       command=head.command)
        ap = AsyncParser(body, head)
        info = ap.ret 
        flag = info['flag']
        delete_terminal_new(dev_id, db, redis)
        if int(flag) == 1: # clear historical data
            clear_data(head.dev_id, db, redis)

        hc = AsyncRespComposer(args)
        request = DotDict(packet=hc.buf,
                          address=address,
                          dev_id=dev_id)
        append_gw_request(request, connection, channel, exchange, gw_binding)
    except:
        logging.exception("[GW] Handle unbind status report exception.")
        GWException().notify()
