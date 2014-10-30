# -*- coding: utf-8 -*-

import logging

from clw.packet.parser.async import AsyncParser
from clw.packet.composer.async import AsyncRespComposer

from helpers.queryhelper import QueryHelper

from error import GWException
from utils.dotdict import DotDict
from utils.public import update_terminal_info
            
from constants import EVENTER, GATEWAY, UWEB, SMS

from utils.misc import get_acc_status_info_key

from handlers.basic import append_gw_request, get_resend_flag

def handle_defend(info, address, connection, channel, exchange, gw_binding, db, redis):
    """
    S18
    defend status report packet
    0: success, then record new terminal's address
    1: invalid SessionID 
    """
    try:
        head = info.head
        body = info.body
        dev_id = head.dev_id

        resend_key, resend_flag = get_resend_flag(redis, dev_id, head.timestamp, head.command) 

        # old version is compatible
        if len(body) == 1:
            body.append('0')
            logging.info("[GW] old version is compatible, append mannual status 0")
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
                defend_info = hp.ret 
                defend_info['mannual_status'] = defend_info['defend_status']
                if defend_info['defend_source'] != 0:
                    # come from sms or web 
                    if defend_info['defend_source'] == "1":
                        _status = u"设防" if defend_info['defend_status'] == "1" else u"撤防"
                        tname = QueryHelper.get_alias_by_tid(head.dev_id, redis, db)
                        sms = SMSCode.SMS_DEFEND_SUCCESS % (tname, _status) 
                        user = QueryHelper.get_user_by_tid(head.dev_id, db)
                        if user:
                            SMSHelper.send(user.owner_mobile, sms)
                    del defend_info['defend_status']
                del defend_info['defend_source']
                update_mannual_status(db, redis, head.dev_id, update_mannual_status)
            update_terminal_status(redis, head.dev_id, address)

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
        logging.exception("[GW] Handle defend status report exception.")
        raise GWException 

