#!/bin/bash
# -*- coding:utf-8 -*-

import os.path
import site

TOP_DIR_ = os.path.abspath(os.path.join(__file__, "../../.."))
site.addsitedir(os.path.join(TOP_DIR_, "libs"))


from urllib import urlencode
import httplib2
import logging
import base64
import time
from decimal import Decimal
from utils.misc import get_push_key, get_alarm_info_key

from tornado.escape import json_encode, json_decode
from tornado.options import define, options, parse_command_line

from helpers.confhelper import ConfHelper
from helpers.queryhelper import QueryHelper


class WSPushHelper(object):

    @staticmethod
    def register(uid, t, key):
        json_data = None
        try:
            url = ConfHelper.PUSH_CONF.register_url
            http = httplib2.Http(timeout=30, disable_ssl_certificate_validation=True)
            data = dict(uid=uid,
                        t=t,
                        key=key)
            headers = {"Content-type": "application/json; charset=utf-8"}
            response, content = http.request(url, 'POST', json_encode(data), headers=headers)
            logging.info("[WSPUSH] Push register response:%s", response)
            logging.info("[WSPUSH] Push register content:%s", content)
            if response['status'] == '200':
                if content:
                    content = content.replace("'",'"')
                    json_data = json_decode(content)
                    if json_data['status_code'] == 200:
                        logging.info("[WSPUSH] Push register uid:%s successfully, response:%s", uid, json_data)
                    else:
                        logging.error("[WSPUSH] Push register uid:%s failed!", uid)
                else:
                    logging.error("[WSPUSH] Push register uid:%s failed!", uid)
            else:
                logging.error("[WSPUSH] Push register uid:%s, response: %s", uid, response)
            
        except Exception as e:
            logging.exception("[WSPUSH] Register failed. Exception: %s", e.args)
        finally:
            return json_data

    @staticmethod
    def push(uid, t, key, packet, message="", badge=""):
        json_data = None
        try:
            url = ConfHelper.PUSH_CONF.push_url
            http = httplib2.Http(timeout=30, disable_ssl_certificate_validation=True)
            data = dict(uid=uid,
                        t=t,
                        key=key,
                        badge=badge,
                        message=message,
                        packet=packet)
            headers = {"Content-type": "application/json; charset=utf-8"}
            response, content = http.request(url, 'POST', json_encode(data), headers=headers)
            if response['status'] == '200':
                if content:
                    content = content.replace("'",'"')
                    json_data = json_decode(content)
                    if json_data['status_code'] == 200:
                        logging.info("[WSPUSH] Push packet successfully! uid = %s, badge = %s, message = %s, packet = %s",
                                     uid, badge, message, packet)
                    else:
                        logging.error("[WSPUSH] Push packet:%s failed!", packet)
                else:
                    logging.error("[WSPUSH] Push packet:%s failed!", packet)
            else:
                logging.error("[WSPUSH] Push packet:%s failed, response: %s failed.", 
                                  packet, response)
        except Exception as e:
            logging.exception("[WSPUSH] Push failed. Exception: %s", e.args)
        finally:
            return json_data

    @staticmethod
    def push_packet(tid, packet, db, redis, t_info=None):
        """Push packet to tid.

        @param: tid
        @param: db 
        @param: redis 
        @param: t_info:{'tid':'',
                        'umobile':'',
                        'group_id':'',
                        'cid':''}
        """
        # NOTE: t_info has higher priority compared with tid
        if not t_info: # tid is avaliable
            t_info = QueryHelper.get_terminal_basic_info(tid, db)

        uid = t_info.get('umobile','')
        cid = t_info.get('cid','')
        
        t = int(time.time()) * 1000
       
        lst = []
        if uid:
            lst.append(uid)
        if cid:
            lst.append(cid)

        for item in set(lst):
            push_key = get_push_key(item, t)
            res = WSPushHelper.push(item, t, push_key, packet)


    @staticmethod
    def pushS3(tid, db, redis, t_info=None):
        """
        S3
        Information about organization.

        @param: tid
        @param: db 
        @param: redis 
        @param: t_info:{'tid':'',
                        'umobile':'',
                        'group_id':'',
                        'cid':''}

        group_1=dict(group_id=1,
                     group_name='jia',
                     tids=['tid1',
                           'tid2', 
                           'tid3'])

        group_2=dict(group_id=2,
                     group_name='jia',
                     tids=['tid1',
                           'tid2', 
                           'tid3'])
        res = []
        res.append(group_1)
        res.append(group_2)
        """
        res = []
        if not t_info:  # tid is avaliable
            t_info = QueryHelper.get_terminal_basic_info(tid, db)

        cid = t_info.get('cid', '')
        
        groups = db.query("SELECT * FROM T_GROUP WHERE corp_id = %s",
                          cid)
        for group in groups:
            terminals = db.query("SELECT * FROM T_TERMINAL_INFO"
                                 "  WHERE group_id = %s "
                                 "  AND service_status= 1", # only success
                                 group['id'])

            tids = []
            for terminal in terminals:
                t = QueryHelper.get_terminal_info(terminal['tid'], db, redis) 
                dct = dict(tid=terminal['tid'],
                           biz_type=t['biz_type'])
                tids.append(dct)
            
            res.append(dict(group_id=group['id'],
                            group_name=group['name'],
                            tids=tids,
                            ))

        packet = dict(packet_type="S3",
                      res=res)

        res = WSPushHelper.push_packet(tid, packet, db, redis, t_info)

    @staticmethod
    def pushS4(tid, db, redis):
        """
        S4
        Information about online, offline.

        res = []
        res.append(dict(tid='tid1',
                        login_status=1))
        res.append(dict(tid='tid2',
                        login_status=2))

        """

        res = [] 
        corp = db.get("SELECT * FROM V_TERMINAL where tid = %s",
                      tid) 
        if corp:
            terminals = db.query("SELECT tid FROM V_TERMINAL WHERE cid= %s",
                                  corp['cid'])
            for terminal in terminals:
                t = QueryHelper.get_terminal_info(terminal['tid'], db, redis) 
                res.append(dict(tid=terminal['tid'],
                                biz_type=t['biz_type'],
                                login_status=t['login']))
        else:
            res = []

        packet = dict(packet_type="S4",
                      res=res)
        res = WSPushHelper.push_packet(tid, packet, db, redis)

    @staticmethod
    def pushS5(tid, body, db, redis):
        """
        S5
        Information about alarm.

        res = []
        res.append(dict(tid=tid,
                        category=2, 
                        pbat=100,
                        type=1,
                        timestamp=1410939622,
                        longitude=419004000,
                        latitude=143676000,
                        clongitude=419004000,
                        clatitude=143676000,
                        name='test name',
                        speed=111,
                        degree=203,
                        gsm=0,
                        locate_error=100,
                        gps=25,
                        alias=111,
                        region_id=11
                    ))

        """
        res = []
        terminal = QueryHelper.get_terminal_info(tid, db, redis)
        body['biz_type'] = terminal['biz_type']

        res.append(body)

        packet = dict(packet_type="S5",
                      res=res)

        res = WSPushHelper.push_packet(tid, packet, db, redis)

    @staticmethod
    def pushS6(tid, db, redis):
        """
        S6
        Information about basic info.

        res = []
        res.append(dict(tid=tid,
                        gps=8,
                        gsm=8,
                        pbat=8,
                        ))

        """
        res = []
        terminal = QueryHelper.get_terminal_info(tid, db, redis)
        packet=dict(tid=tid,
                    biz_type=terminal['biz_type'],
                    gps=terminal['gps'],
                    gsm=terminal['gsm'],
                    pbat=terminal['pbat'])
        res.append(packet)

        packet = dict(packet_type="S6",
                      res=res)

        res = WSPushHelper.push_packet(tid, packet, db, redis)

    @staticmethod
    def pushS7(tid, db, redis):
        """
        S7
        Information about basic info.

        res = []
        res.append(dict(tid=tid,
                        alias='jiajiajia',
                        icon_type=2,
                        owner_mobile='13011292217',
                        mannual_status=1,
                        ))
        """
        res = []
        terminal = QueryHelper.get_terminal_info(tid, db, redis)
        packet=dict(tid=tid,
                    biz_type=terminal['biz_type'],
                    alias=terminal['alias'],
                    icon_type=terminal['icon_type'],
                    owner_mobile=terminal['owner_mobile'],
                    mannual_status=terminal['mannual_status'])

        res.append(packet)

        packet = dict(packet_type="S7",
                      res=res)
        res = WSPushHelper.push_packet(tid, packet, db, redis)

    @staticmethod
    def pushS8(tid, acc_message, db, redis):
        """
        S8
        Information about acc info.

        res=dict(tid=tid,
                 acc_message=1))
        """
        res=dict(tid=tid,
                 acc_message=acc_message)

        packet = dict(packet_type="S8",
                      res=res)
        res = WSPushHelper.push_packet(tid, packet, db, redis)


if __name__ == '__main__':
    ConfHelper.load('../../conf/global.conf')
    parse_command_line()

    uid = 1
    t = 1
    key = 1
    res = WSPushHelper.register(uid, t, key)
