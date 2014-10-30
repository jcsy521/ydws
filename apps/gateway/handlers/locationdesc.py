# -*- coding: utf-8 -*-

import logging

from clw.packet.parser.locationdesc import LocationDescParser
from clw.packet.composer.locationdesc import LocationDescRespComposer

from error import GWException

from helpers.queryhelper import QueryHelper

from error import GWException
from utils.dotdict import DotDict
from utils.public import update_terminal_info
            
from constants import EVENTER, GATEWAY, UWEB, SMS

from utils.misc import get_acc_status_info_key
            
from handlers.basic import append_gw_request, get_resend_flag

def handle_locationdesc(info, address, connection, channel, exchange, gw_binding, db, redis):
    """
    S10
    locationdesc packet

    0: success, then return locationdesc to terminal and record new terminal's address
    1: invalid SessionID 
    """
    try:
        head = info.head
        body = info.body
        dev_id = head.dev_id
        if len(body) == 6:
            body.append(20) 
            logging.info("[GW] old version is compatible, append locate_error")

        resend_key, resend_flag = get_resend_flag(redis, dev_id, head.timestamp, head.command) 

        go_ahead = False 
        args = DotDict(success=GATEWAY.RESPONSE_STATUS.SUCCESS,
                       locationdesc="",
                       ew="E",
                       lon=0.0,
                       ns="N",
                       lat=0.0)
        sessionID = QueryHelper.get_terminal_sessionID(dev_id, redis)
        if sessionID != head.sessionID:
            args.success = GATEWAY.RESPONSE_STATUS.INVALID_SESSIONID
            logging.error("[GW] Invalid sessionID, terminal: %s", head.dev_id)
        else:
            if resend_flag:
                logging.warn("[GW] Recv resend packet, head: %s, body: %s and drop it!",
                             info.head, info.body)
            else:
                go_ahead = True


        #NOTE: Check ydcw or ajt 
        ajt = QueryHelper.get_ajt_whitelist_by_mobile(head.dev_id, db) 
        if ajt: 
            url_out = ConfHelper.UWEB_CONF.ajt_url_out 
        else: 
            url_out = ConfHelper.UWEB_CONF.url_out

        if go_ahead:
            redis.setvalue(resend_key, True, GATEWAY.RESEND_EXPIRY)
            ldp = LocationDescParser(body, head)
            location = ldp.ret
            logging.info("[GW] T10 packet parsered:%s", location)
            if not  location.has_key('gps_time'):
                location['gps_time'] = int(time.time())
                logging.info("[GW] what's up? location:%s hasn't gps_time.", location)
            location['t'] = EVENTER.INFO_TYPE.POSITION
            if location['valid'] != GATEWAY.LOCATION_STATUS.SUCCESS:
                cellid = True
            else:
                cellid = False
            location = lbmphelper.handle_location(location, redis, cellid=cellid, db=db)
            location.name = location.get('name') if location.get('name') else ""
            location.name = safe_unicode(location.name)
            user = QueryHelper.get_user_by_tid(head.dev_id, db)
            tname = QueryHelper.get_alias_by_tid(head.dev_id, redis, db)
            dw_method = u'GPS' if not cellid else u'基站'
            if location.cLat and location.cLon:
                if user:
                    current_time = get_terminal_time(int(time.time()))
                    sms = SMSCode.SMS_DW_SUCCESS % (tname, dw_method,
                                                    location.name, 
                                                    safe_unicode(current_time)) 
                    url = url_out + '/wapimg?clon=' +\
                          str(location.cLon/3600000.0) + '&clat=' + str(location.cLat/3600000.0)
                    tiny_id = URLHelper.get_tinyid(url)
                    if tiny_id:
                        base_url = url_out + UWebHelper.URLS.TINYURL
                        tiny_url = base_url + '/' + tiny_id
                        logging.info("[GW] get tiny url successfully. tiny_url:%s", tiny_url)
                        redis.setvalue(tiny_id, url, time=EVENTER.TINYURL_EXPIRY)
                        sms += u"点击 " + tiny_url + u" 查看定位器位置。" 
                    else:
                        logging.info("[GW] get tiny url failed.")
                    SMSHelper.send(user.owner_mobile, sms)
            else:
                if user:
                    sms = SMSCode.SMS_DW_FAILED % (tname, dw_method)
                    SMSHelper.send(user.owner_mobile, sms)
            if not (location.lat and location.lon):
                args.success = GATEWAY.RESPONSE_STATUS.CELLID_FAILED
            else:
                insert_location(location, db, redis)

        lc = LocationDescRespComposer(args)
        request = DotDict(packet=lc.buf,
                          address=address,
                          dev_id=dev_id)
        update_terminal_status(redis, head.dev_id, address)
        append_gw_request(request, connection, channel, exchange, gw_binding)
    except:
        logging.exception("[GW] Handle locationdesc exception.")
        raise GWException
