# -*- coding: utf-8 -*-
import logging

from clw.packet.parser.unusualactivate import UnusualActivateParser
from clw.packet.composer.unusualactivate import UnusualActivateComposer

from helpers.queryhelper import QueryHelper
from helpers.smshelper import SMSHelper 

from error import GWException
from utils.dotdict import DotDict
from utils.public import update_terminal_info
            
from constants import EVENTER, GATEWAY, UWEB, SMS

from utils.misc import get_acc_status_info_key

from handlers.basic import append_gw_request, get_resend_flag, update_terminal_status

def handle_unusual(info, address, connection, channel, exchange, gw_binding, db, redis):
    """Unusual activate report packet: owner_mobile changed.
    S27 
    NOTE: deprecated 

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
        if resend_flag:
            logging.warn("[GW] Recv resend packet, head: %s, body: %s and drop it!",
                         info.head, info.body)
        else: 
            redis.setvalue(resend_key, True, GATEWAY.RESEND_EXPIRY)
            uap = UnusualActivateParser(body, head)
            t_info = uap.ret
            terminal = db.get("SELECT mobile FROM T_TERMINAL_INFO"
                              "  WHERE tid = %s LIMIT 1",
                              t_info['dev_id'])
            if terminal:
                sms = SMSCode.SMS_UNUSUAL_ACTIVATE % terminal['mobile'] 
                SMSHelper.send(t_info['u_msisdn'], sms)
            else:
                logging.error("[GW] Terminal: %s is not existent, what's up?", t_info['dev_id'])

        uac = UnusualActivateComposer(args)
        request = DotDict(packet=uac.buf,
                          address=address,
                          dev_id=dev_id)
        append_gw_request(request, connection, channel, exchange, gw_binding)
    except:
        logging.exception("[GW] Hand unusual activate report exception.")
        GWException().notify()
