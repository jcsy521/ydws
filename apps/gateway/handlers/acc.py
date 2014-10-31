# -*- coding: utf-8 -*-

import logging

from clw.packet.parser.acc_status import ACCStatusParser
from clw.packet.composer.acc_status import ACCStatusComposer

from helpers.queryhelper import QueryHelper
from helpers.wspushhelper import WSPushHelper
            
from error import GWException

from utils.dotdict import DotDict
from utils.public import update_terminal_info
            
from constants import EVENTER, GATEWAY, UWEB, SMS

from utils.misc import get_acc_status_info_key

from handlers.basic import append_gw_request 

def handle_acc_status(info, address, connection, channel, exchange, gw_binding, db, redis):
    """
    S30
    ACC_status: 

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
            uap = ACCStatusParser(body, head)
            t_info = uap.ret
            acc_status_info_key = get_acc_status_info_key(dev_id)
            acc_status_info = redis.getvalue(acc_status_info_key)
            if acc_status_info:  
                acc_status_info['op_status'] = 1 # success
                redis.setvalue(acc_status_info_key, acc_status_info, UWEB.ACC_STATUS_EXPIRY)
                WSPushHelper.pushS8(dev_id, 1, db, redis)
            else: # It should never occur. 
                logging.error("[GW] ACC_status can not be found. dev_id: %s",
                              dev_id)
                pass

        asc = ACCStatusComposer(args)
        request = DotDict(packet=asc.buf,
                          address=address,
                          dev_id=dev_id)
        append_gw_request(request, connection, channel, exchange, gw_binding)
    except:
        logging.exception("[GW] Handle acc status exception.")
        raise GWException

def handle_acc_status_report(info, address, connection, channel, exchange, gw_binding, db, redis):
    """
    S31
    ACC_status_report: 

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
            uap = ACCStatusReportParser(body, head)
            t_info = uap.ret
            #NOTE: Just record it in db.
            db.execute("INSERT INTO T_ACC_STATUS_REPORT(tid, category, timestamp)"
                       "  VALUES(%s, %s, %s)",
                       t_info['dev_id'], t_info['category'], t_info['timestamp'])
        asc = ACCStatusReportComposer(args)
        request = DotDict(packet=asc.buf,
                          address=address,
                          dev_id=dev_id)
        append_gw_request(request, connection, channel, exchange, gw_binding)
    except:
        logging.exception("[GW] Handle acc status report exception.")
        raise GWException

