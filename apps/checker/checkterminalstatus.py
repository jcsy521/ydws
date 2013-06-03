#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os.path
import site
import logging
import time

TOP_DIR_ = os.path.abspath(os.path.join(__file__, "../../../.."))
site.addsitedir(os.path.join(TOP_DIR_, "libs"))

from db_.mysql import DBConnection
from utils.myredis import MyRedis
from utils.dotdict import DotDict
from utils.misc import get_offline_lq_key, get_lq_interval_key,\
     get_terminal_sessionID_key, get_terminal_info_key, get_terminal_address_key,\
     get_terminal_time
from constants import GATEWAY, EVENTER, UWEB, SMS
from codes.smscode import SMSCode
from helpers.smshelper import SMSHelper
from helpers.queryhelper import QueryHelper

class CheckTerminalStatus(object):
    def __init__(self):
        self.db = DBConnection().db
        self.redis = MyRedis()
        self.domain_ip = '211.139.215.236:10025'

    def check_terminal_status(self):
        try:
            terminals = self.db.query("SELECT tid, domain FROM T_TERMINAL_INFO"
                                      "  WHERE login != %s",
                                      GATEWAY.TERMINAL_LOGIN.OFFLINE)
            for terminal in terminals:
                terminal_status_key = get_terminal_address_key(terminal.tid)
                status = self.redis.getvalue(terminal_status_key)
                offline_lq_key = get_offline_lq_key(terminal.tid)
                offline_lq_time = self.redis.getvalue(offline_lq_key)
                if not status:
                    if not offline_lq_time:
                        self.send_cq_sms(terminal.tid, terminal.domain)
                        self.redis.setvalue(offline_lq_key, int(time.time()), 15*60)
                    elif (time.time() - offline_lq_time) > 10 * 60:
                        self.heartbeat_lost_report(terminal.tid)
                        self.redis.delete(offline_lq_key)
                    else:
                        pass
        except KeyboardInterrupt:
            logging.error("Ctrl-C is pressed.")
        except:
            logging.exception("[CK] Check terminal status exception.")

    def send_cq_sms(self, tid, domain):
        terminal_info = QueryHelper.get_terminal_info(tid, self.db, self.redis)
        if (terminal_info['pbat']) >= 5 and (domain != self.domain_ip):
            sms_cq = SMSCode.SMS_CQ
            sms_domain = SMSCode.SMS_DOMAIN % self.domain_ip 
            mobile = terminal_info['mobile']
            SMSHelper.send_to_terminal(mobile, sms_cq)
            SMSHelper.send_to_terminal(mobile, sms_domain)
            self.db.execute("UPDATE T_TERMINAL_INFO SET domain = %s"
                            "  WHERE tid = %s",
                            self.domain_ip, tid)
            logging.info("[CK] Send cq and domain sms to mobile: %s", mobile)

    def send_lq_sms(self, tid):
        sim = QueryHelper.get_tmobile_by_tid(tid, self.redis, self.db)
        if sim:
            interval = SMS.LQ.WEB
            sms = SMSCode.SMS_LQ % interval 
            SMSHelper.send_to_terminal(sim, sms)
            lq_interval_key = get_lq_interval_key(tid)
            self.redis.setvalue(lq_interval_key, int(time.time()), (interval*60 - 160))
            logging.info("[CK] Send offline LQ: '%s' to Sim: %s", sms, sim)
                
    def heartbeat_lost_report(self, tid):
        timestamp = int(time.time())
        rname = EVENTER.RNAME.HEARTBEAT_LOST
        category = EVENTER.CATEGORY[rname]
        lid = self.db.execute("INSERT INTO T_LOCATION(tid, timestamp, category, type)"
                              "  VALUES(%s, %s, %s, %s)",
                              tid, timestamp, category, 1)
        self.db.execute("INSERT INTO T_EVENT(tid, lid, category)"
                        "  VALUES (%s, %s, %s)",
                        tid, lid, category)
        user = QueryHelper.get_user_by_tid(tid, self.db)
        if user:
            sms_option = QueryHelper.get_sms_option_by_uid(user.owner_mobile, 'heartbeat_lost', self.db)
            logging.info("sms option: %s of %s", sms_option, user.owner_mobile)
            if sms_option.heartbeat_lost == UWEB.SMS_OPTION.SEND:
                current_time = get_terminal_time(timestamp) 
                tname = QueryHelper.get_alias_by_tid(tid, self.redis, self.db)
                sms = SMSCode.SMS_HEARTBEAT_LOST % (tname, current_time)
                SMSHelper.send(user.owner_mobile, sms)
                corp = self.db.get("SELECT T_CORP.mobile FROM T_CORP, T_GROUP, T_TERMINAL_INFO"
                                   "  WHERE T_TERMINAL_INFO.tid = %s"
                                   "    AND T_TERMINAL_INFO.group_id != -1"
                                   "    AND T_TERMINAL_INFO.group_id = T_GROUP.id"
                                   "    AND T_GROUP.corp_id = T_CORP.cid",
                                   tid)
                if (corp and corp.mobile != user.owner_mobile):
                    SMSHelper.send(corp.mobile, sms)
        logging.warn("[CK] Terminal %s Heartbeat lost!!!", tid)
        # memcached clear sessionID
        terminal_sessionID_key = get_terminal_sessionID_key(tid)
        self.redis.delete(terminal_sessionID_key)
        # db set offline 
        info = DotDict(tid=tid,
                       login=GATEWAY.TERMINAL_LOGIN.OFFLINE,
                       offline_time=timestamp)
        self.update_terminal_status(info)

    def update_terminal_status(self, info):
        terminal_info_key = get_terminal_info_key(info['tid'])
        terminal_info = self.redis.getvalue(terminal_info_key)
        if not terminal_info:
            terminal_info = self.db.get("SELECT mannual_status, defend_status,"
                                        "  fob_status, mobile, login, gps, gsm,"
                                        "  pbat, keys_num"
                                        "  FROM T_TERMINAL_INFO"
                                        "  WHERE tid = %s", info['tid'])
            car = self.db.get("SELECT cnum FROM T_CAR"
                              "  WHERE tid = %s", info['tid'])
            fobs = self.db.query("SELECT fobid FROM T_FOB"
                                 "  WHERE tid = %s", info['tid'])
            terminal_info = DotDict(terminal_info)
            terminal_info['alias'] = car.cnum if car.cnum else terminal_info.mobile
            terminal_info['fob_list'] = [fob.fobid for fob in fobs]

        # db
        self.db.execute("UPDATE T_TERMINAL_INFO"
                        "  SET login = %s," 
                        "      offline_time = %s"
                        "  WHERE tid = %s",
                        info['login'], info['offline_time'], info['tid'])
        # redis
        logging.info("[CK] %s before set redis login: %s, login: %s",
                     info['tid'], terminal_info['login'], info['login'])
        terminal_info['login'] = info['login'] 
        self.redis.setvalue(terminal_info_key, terminal_info)
        terminal_info = self.redis.getvalue(terminal_info_key)
        logging.info("[CK] %s after set redis login: %s", info['tid'], terminal_info['login'])

