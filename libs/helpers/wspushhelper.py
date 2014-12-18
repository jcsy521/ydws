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
    def register(uid, t, key, redis):
        """Core method. 
        """
        json_data = dict(data=dict(push_id='dummy',
                                   psd='dummy'))
        try:
            url = ConfHelper.PUSH_CONF.register_url
            http = httplib2.Http(timeout=3, disable_ssl_certificate_validation=True)
            data = dict(uid=uid,
                        t=t,
                        key=key)
            headers = {"Content-type": "application/json; charset=utf-8"}
            response, content = http.request(
                url, 'POST', json_encode(data), headers=headers)
            logging.info("[WSPUSH] Push register response:%s", response)
            logging.info("[WSPUSH] Push register content:%s", content)
            if response['status'] == '200':
                if content:
                    content = content.replace("'", '"')
                    json_data = json_decode(content)
                    if json_data['status_code'] == 200:
                        logging.info(
                            "[WSPUSH] Push register uid:%s successfully, response:%s", uid, json_data)
                        # NOTE: keep the account in redis.
                        redis.setvalue('wspush_registered:%s' %
                                       uid, True, 60 * 60 * 24)
                    else:
                        logging.error(
                            "[WSPUSH] Push register uid:%s failed!", uid)
                else:
                    logging.error("[WSPUSH] Push register uid:%s failed!", uid)
            else:
                logging.error(
                    "[WSPUSH] Push register uid:%s, response: %s", uid, response)

        except Exception as e:
            logging.exception(
                "[WSPUSH] Register failed. Exception: %s", e.args)
        finally:
            return json_data

    @staticmethod
    def push(uid, t, key, packet, redis, message="", badge=""):
        """Core method. 
        """
        json_data = None
        try:
            is_registered = redis.getvalue('wspush_registered:%s' % uid)
            if not is_registered:
                logging.info("[WSPUSH] Uid has not registered, ignore it. uid: %s", 
                             uid)
                return json_data

            url = ConfHelper.PUSH_CONF.push_url
            http = httplib2.Http(timeout=3, disable_ssl_certificate_validation=True)
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
                    content = content.replace("'", '"')
                    json_data = json_decode(content)
                    if json_data['status_code'] == 200:
                        logging.info("[WSPUSH] Push packet successfully! uid = %s, badge = %s, message = %s, packet = %s",
                                     uid, badge, message, packet)
                    else:
                        logging.error("[WSPUSH] Push packet:%s failed!", 
                                       packet)
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
    def register_wspush(uid, redis):
        """Register account in WSpush. 
        """
        t = int(time.time()) * 1000
        key = get_push_key(uid, t)
        res = WSPushHelper.register(uid, t, key, redis)
        return res

    @staticmethod
    def push_packet(tid, packet, db, redis, t_info=None):
        """Push packet to tid.

        :arg tid: string
        :arg db: database instance 
        :arg redis: redis instance
        :arg t_info: dict, e.g.

            {
               'tid':'',
               'umobile':'',
               'group_id':'',
               'cid':''
            }
 
        """
        # NOTE: t_info has higher priority compared with tid
        if not t_info:  # tid is avaliable
            t_info = QueryHelper.get_terminal_basic_info(tid, db)

        uid = t_info.get('umobile', '')
        cid = t_info.get('cid', '')

        t = int(time.time()) * 1000

        lst = []

        if uid:
            lst.append(uid)
        if cid:
            lst.append(cid)    

        for item in set(lst):
            push_key = get_push_key(item, t)
            res = WSPushHelper.push(item, t, push_key, packet, redis)

    @staticmethod
    def pushS3(tid, db, redis, t_info=None):
        """
        S3
        Information about organization.

        :arg tid: string
        :arg db: database instance
        :arg redis: redis instance
        :arg t_info: dict, record the terminal's basic info. it has higher privilege then tid. e.g.

            {
                'tid':'',
                'umobile':'',
                'group_id':'',
                'cid':''
            }

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
                                 "  AND service_status= 1",  # only success
                                 group['id'])

            tids = []
            for terminal in terminals:
                t = QueryHelper.get_terminal_info(terminal['tid'], db, redis)
                dct = dict(tid=terminal['tid'],
                           biz_type=t.get('biz_type', 0))
                tids.append(dct)

            res.append(dict(group_id=group['id'],
                            group_name=group['name'],
                            tids=tids,
                            ))

        packet = dict(packet_type="S3",
                      res=res)

        res = WSPushHelper.push_packet(tid, packet, db, redis, t_info)

    @staticmethod
    def pushS3_dummy(uids, db, redis):
        """
        S3
        Wspush a dummy s3 packet to individuals.

        :arg uids: list. e.g.
            [
                'xxx',
                'yyy'
            ]
        :arg db: database instance
        :arg redis: redis instance
        """

        t = int(time.time()) * 1000

        packet = dict(packet_type="S3",
                      res=[])
        
        for item in uids:
            push_key = get_push_key(item, t)
            res = WSPushHelper.push(item, t, push_key, packet, redis)

    @staticmethod
    def pushS4(tid, db, redis):
        """
        S4
        Information about online, offline.

        e.g.

        res = []
        res.append(dict(tid='tid1',
                        login_status=1))
        res.append(dict(tid='tid2',
                        login_status=2))

        """

        res = []

        t = QueryHelper.get_terminal_info(tid, db, redis)
        if t:
            res.append(dict(tid=tid,
                            biz_type=t.get('biz_type', 0),
                            login_status=t['login']))

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
        body['biz_type'] = terminal.get('biz_type', 0)

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
        packet = dict(tid=tid,
                      biz_type=terminal.get('biz_type', 0),
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
        packet = dict(tid=tid,
                      biz_type=terminal.get('biz_type', 0),
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
        res = dict(tid=tid,
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
