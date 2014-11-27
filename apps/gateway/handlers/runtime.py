# -*- coding: utf-8 -*-

import logging

from clw.packet.parser.async import AsyncParser
from clw.packet.composer.runtime import RuntimeRespComposer

from helpers.queryhelper import QueryHelper

from error import GWException
from utils.dotdict import DotDict
from utils.public import update_terminal_info
            
from constants import EVENTER, GATEWAY, UWEB, SMS

from utils.misc import get_acc_status_info_key, get_resend_key

from handlers.basic import append_gw_request, get_resend_flag

def handle_runtime(info, address, connection, channel, exchange, gw_binding, db, redis):
    """
    S23
    runtime status packet: {login [0:unlogin | 1:login],
                            defend_status [0:undefend | 1:defend],
                            gps:gsm:pbat [0-100:0-9:0-100]} 

    0: success, then record new terminal's address
    1: invalid SessionID
    """
    try:
        head = info.head
        body = info.body
        dev_id = head.dev_id
        resend_key, resend_key = get_resend_flag(redis, dev_id, head.timestamp, head.command)
        if len(body) == 3:
            body.append('-1')
            body.append('0')
            logging.info("[GW] old version is compatible, append fob_pbat, is_send")
        if len(body) == 4:
            body.append('0')
            logging.info("[GW] old version is compatible, append is_send")
        args = DotDict(success=GATEWAY.RESPONSE_STATUS.SUCCESS,
                       command=head.command,
                       mannual_status='')
        sessionID = QueryHelper.get_terminal_sessionID(dev_id, redis)
        if sessionID != head.sessionID:
            args.success = GATEWAY.RESPONSE_STATUS.INVALID_SESSIONID 
        else:
            if resend_flag:
                logging.warn("[GW] Recv resend packet, head: %s, body: %s and drop it!",
                             info.head, info.body)
                terminal_info = QueryHelper.get_terminal_info(head.dev_id, db, redis)
                args.mannual_status = terminal_info['mannual_status']
            else:
                redis.setvalue(resend_key, True, GATEWAY.RESEND_EXPIRY)
                hp = AsyncParser(body, head)
                runtime_info = hp.ret 
                update_terminal_status(redis, head.dev_id, address)
                terminal_info = update_terminal_info(db, redis, runtime_info)
                args.mannual_status = terminal_info['mannual_status']
                db.execute("INSERT INTO T_RUNTIME_STATUS"
                           "  VALUES(NULL, %s, %s, %s, %s, %s, %s, %s, %s)",
                           head.dev_id, runtime_info['login'], runtime_info['defend_status'],
                           runtime_info['gps'], runtime_info['gsm'], runtime_info['pbat'],
                           runtime_info['fob_pbat'], head.timestamp)

                is_send = int(runtime_info['is_send'])
                if is_send:
                    terminal_info_key = get_terminal_info_key(head.dev_id) 
                    terminal_info = QueryHelper.get_terminal_info(head.dev_id, db, redis)
                    alias = QueryHelper.get_alias_by_tid(head.dev_id, redis, db)
                    communication_staus = u'正常'
                    communication_mode = u'撤防'
                    gsm_strength = u'强'
                    gps_strength = u'强'
                    if int(terminal_info['login']) == GATEWAY.TERMINAL_LOGIN.ONLINE:
                        communication_staus = u'正常'
                    else:
                        communication_staus = u'异常'

                    if int(terminal_info['mannual_status']) == UWEB.DEFEND_STATUS.YES:
                        communication_mode = u'强力设防'
                    elif int(terminal_info['mannual_status']) == UWEB.DEFEND_STATUS.SMART:
                        communication_mode = u'智能设防'
                    else:
                        communication_mode= u'撤防'

                    pbat = int(terminal_info.get('pbat', 0))

                    gsm = int(terminal_info.get('gsm', 0))
                    if gsm < 3:
                        gsm_strength = u'弱'
                    elif gsm < 6:
                        gsm_strength = u'较弱'

                    gps = int(terminal_info.get('gps', 0))
                    if gps < 10:
                        gps_strength = u'弱' 
                    elif gps < 20:
                        gps_strength = u'较弱' 
                    elif gps < 30:
                        gps_strength = u'较强' 

                    runtime_sms = SMSCode.SMS_RUNTIME_STATUS % (alias, communication_staus, communication_mode, int(pbat), gsm_strength, gps_strength)
                    SMSHelper.send(terminal_info.owner_mobile, runtime_sms)
                    logging.info("[GW] Send runtime_status sms to user: %s, tid: %s",
                                 terminal_info.owner_mobile, head.dev_id)

            update_terminal_status(redis, head.dev_id, address)

        if args['success'] == GATEWAY.RESPONSE_STATUS.SUCCESS: 
            acc_status_info_key = get_acc_status_info_key(dev_id) 
            acc_status_info = redis.getvalue(acc_status_info_key) 
            if acc_status_info and (not acc_status_info['t2_status']): # T2(query) is need
                args['success'] = 3 # acc_status is changed 
                logging.info("[GW] ACC_status is changed, dev_id: %s, acc_status_info: %s", 
                             dev_id, acc_status_info)

        rc = RuntimeRespComposer(args)
        request = DotDict(packet=rc.buf,
                          address=address,
                          dev_id=dev_id)
        append_gw_request(request, connection, channel, exchange, gw_binding)
    except:
        logging.exception("[GW] Handle runtime status report exception.")
        raise GWException
