# -*- coding: utf-8 -*-

import logging

from error import GWException

from clw.packet.parser.misc import MiscParser
from clw.packet.composer.misc import MiscComposer

from helpers.queryhelper import QueryHelper
            
from utils.dotdict import DotDict
from utils.public import update_terminal_info
            
from constants import EVENTER, GATEWAY, UWEB, SMS

from utils.misc import get_acc_status_info_key

from handlers.basic import append_gw_request 
            
def handle_misc(info, address, connection, channel, exchange, gw_binding, db, redis):
    """
    S28
    misc: debugging for terminal.

    0: success, then record new terminal's address
    1: invalid SessionID 
    """
    try:
        head = info.head
        body = info.body
        dev_id = head.dev_id

        args = DotDict(success=GATEWAY.RESPONSE_STATUS.SUCCESS,
                       command=head.command)
        sessionID = QueryHelper.get_terminal_sessionID(dev_id, redis)
        if sessionID != head.sessionID: 
            args.success = GATEWAY.RESPONSE_STATUS.INVALID_SESSIONID
            logging.error("[GW] Invalid sessionID, terminal: %s", head.dev_id)
        else:
            uap = MiscParser(body, head)
            t_info = uap.ret
            db.execute("UPDATE T_TERMINAL_INFO"
                       " SET misc = %s"
                       "    WHERE tid = %s ",
                       t_info['misc'], head.dev_id)

        if args['success'] == GATEWAY.RESPONSE_STATUS.SUCCESS: 
            acc_status_info_key = get_acc_status_info_key(dev_id) 
            acc_status_info = redis.getvalue(acc_status_info_key) 
            if acc_status_info and (not acc_status_info['t2_status']): # T2(query) is need
                args['success'] = 3 # acc_status is changed 
                logging.info("[GW] ACC_status is changed, dev_id: %s, acc_status_info: %s", 
                             dev_id, acc_status_info)
        uac = MiscComposer(args)
        request = DotDict(packet=uac.buf,
                          address=address,
                          dev_id=dev_id)
        append_gw_request(request, connection, channel, exchange, gw_binding)
    except:
        logging.exception("[GW] Handle misc report exception.")
        GWException().notify()
