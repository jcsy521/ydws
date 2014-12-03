#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os.path
import site
import logging
import time

TOP_DIR_ = os.path.abspath(os.path.join(__file__, "../../.."))
site.addsitedir(os.path.join(TOP_DIR_, "libs"))

from tornado.options import define, options, parse_command_line

from db_.mysql import DBConnection
from utils.myredis import MyRedis
from utils.dotdict import DotDict
from utils.misc import (get_offline_lq_key, get_lq_interval_key,
     get_terminal_sessionID_key, get_terminal_info_key, get_terminal_address_key,
     get_terminal_time, safe_unicode, get_alarm_info_key)
from constants import GATEWAY, EVENTER, UWEB, SMS
from codes.smscode import SMSCode
from helpers.smshelper import SMSHelper
from helpers.emailhelper import EmailHelper 
from helpers.lbmphelper import get_latlon_from_cellid
from helpers.queryhelper import QueryHelper
from helpers.wspushhelper import WSPushHelper
from helpers.confhelper import ConfHelper

if not 'conf' in options:
    define('conf', default=os.path.join(TOP_DIR_, "conf/global.conf"))


class CheckTerminalStatus(object):

    def __init__(self):
        self.db = DBConnection().db
        self.redis = MyRedis()
        self.domain_ip = ConfHelper.GW_SERVER_CONF.domain_ip 

    def check_terminal_status(self):
        """Check terminal whether lose hearbeat and provide reminder for
        associated staff.
        """
        try:
            terminals = self.db.query("SELECT tid, domain FROM T_TERMINAL_INFO"
                                      "  WHERE login != %s"
                                      "    AND service_status = 1",
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
        """Send CQ sms to terminal.
        """
        terminal_info = QueryHelper.get_terminal_info(tid, self.db, self.redis)
        if terminal_info['pbat'] >= 5:
            mobile = terminal_info['mobile']
            sms_cq = SMSCode.SMS_CQ
            if len(mobile) != 11:
                return
            biz_type = QueryHelper.get_biz_type_by_tmobile(mobile, self.db) 
            if biz_type != UWEB.BIZ_TYPE.YDWS: 
                return
            SMSHelper.send_to_terminal(mobile, sms_cq)
            logging.info("[CK] Send cq sms to mobile: %s", mobile)

            #NOTE: Some mobiles is not cq
            back_list = ['13926952102']
            if domain != self.domain_ip:
                if mobile in back_list: 
                    logging.info("do not set domain to mobile: %s", mobile)
                    return
                sms_domain = SMSCode.SMS_DOMAIN % self.domain_ip 
                SMSHelper.send_to_terminal(mobile, sms_domain)
                self.db.execute("UPDATE T_TERMINAL_INFO SET domain = %s"
                                "  WHERE tid = %s",
                                self.domain_ip, tid)
                logging.info("[CK] Send domain sms: %s to mobile: %s",
                             sms_domain, mobile)

    def send_lq_sms(self, tid):
        """Send LQ sms to terminal.
        """
        sim = QueryHelper.get_tmobile_by_tid(tid, self.redis, self.db)
        if sim:
            interval = SMS.LQ.WEB
            sms = SMSCode.SMS_LQ % interval 
            biz_type = QueryHelper.get_biz_type_by_tmobile(sim, self.db)
            if biz_type != UWEB.BIZ_TYPE.YDWS:
                pass
            else:
                SMSHelper.send_to_terminal(sim, sms)
            lq_interval_key = get_lq_interval_key(tid)
            self.redis.setvalue(lq_interval_key, int(time.time()), (interval*60 - 160))
            logging.info("[CK] Send offline LQ: '%s' to Sim: %s", sms, sim)
                
    def heartbeat_lost_report(self, tid):
        """Recort the heartbeat-lost event and remind the associated staff.
        """
        #NOTE: wspush to client 
        WSPushHelper.pushS4(tid, self.db, self.redis)


        timestamp = int(time.time())
        rname = EVENTER.RNAME.HEARTBEAT_LOST
        category = EVENTER.CATEGORY[rname]
        lid = self.db.execute("INSERT INTO T_LOCATION(tid, timestamp, category, type)"
                              "  VALUES(%s, %s, %s, %s)",
                              tid, timestamp, category, 1)
        self.db.execute("INSERT INTO T_EVENT(tid, timestamp, lid, category)"
                        "  VALUES (%s, %s, %s, %s)",
                        tid, timestamp, lid, category)
        
        # keep alarm info 
        alarm = dict(tid=tid, 
                     category=6, 
                     type=1, #cellid 
                     timestamp=timestamp, 
                     latitude=0, 
                     longitude=0, 
                     clatitude=0, 
                     clongitude=0, 
                     name=u'', 
                     degree=0, 
                     speed=0)
        # get last_location
        last_location = QueryHelper.get_location_info(tid, self.db, self.redis)
        if last_location:
            alarm['type'] = 0 # gps
            alarm['latitude'] = last_location['latitude'] 
            alarm['longitude'] = last_location['longitude'] 
            alarm['clatitude'] = last_location['clatitude']
            alarm['clongitude'] = last_location['clongitude']
            alarm['name'] = last_location['name']
            alarm['degree'] = last_location['degree'] 
            alarm['speed'] = last_location['speed']

        alarm_info_key = get_alarm_info_key(alarm['tid']) 
        alarm_info = self.redis.getvalue(alarm_info_key) 
        alarm_info = alarm_info if alarm_info else [] 
        alarm['keeptime'] = int(time.time())
        alarm_info.append(alarm)
        alarm_info_new = [] 
        for alarm in alarm_info: 
            if alarm.get('keeptime', None) is None: 
                alarm['keeptime'] = alarm['timestamp'] 
            if alarm['keeptime'] + 60*10 < int(time.time()): 
                pass 
            else: 
                alarm_info_new.append(alarm)
        self.redis.setvalue(alarm_info_key, alarm_info_new, EVENTER.ALARM_EXPIRY)

        # remind owner
        user = QueryHelper.get_user_by_tid(tid, self.db)
        if user:
            sms_option = QueryHelper.get_sms_option_by_uid(user.owner_mobile, 'heartbeat_lost', self.db)
            logging.info("sms option: %s of %s", sms_option, user.owner_mobile)
            if sms_option == UWEB.SMS_OPTION.SEND:
                current_time = get_terminal_time(timestamp) 
                current_time = safe_unicode(current_time)
                tname = QueryHelper.get_alias_by_tid(tid, self.redis, self.db)
                sms = SMSCode.SMS_HEARTBEAT_LOST % (tname, current_time)
                SMSHelper.send(user.owner_mobile, sms)

                #NOTE: if it's a monitored of ydwq, will receive a sms.
                terminal = QueryHelper.get_terminal_info(tid, self.db, self.redis) 
                mobile = terminal['mobile']
                biz_type = QueryHelper.get_biz_type_by_tmobile(mobile, self.db)
                if biz_type != UWEB.BIZ_TYPE.YDWS:
                    sms = SMSCode.SMS_HEARTBEAT_LOST_YDWQ % (tname, current_time)
                    SMSHelper.send(mobile, sms)
                
                #corp = self.db.get("SELECT T_CORP.mobile FROM T_CORP, T_GROUP, T_TERMINAL_INFO"
                #                   "  WHERE T_TERMINAL_INFO.tid = %s"
                #                   "    AND T_TERMINAL_INFO.group_id != -1"
                #                   "    AND T_TERMINAL_INFO.group_id = T_GROUP.id"
                #                   "    AND T_GROUP.corp_id = T_CORP.cid",
                #                   tid)
                #if (corp and corp.mobile != user.owner_mobile):
                #    SMSHelper.send(corp.mobile, sms)

        logging.warn("[CK] Terminal %s Heartbeat lost!!!", tid)
        # memcached clear sessionID
        terminal_sessionID_key = get_terminal_sessionID_key(tid)
        self.redis.delete(terminal_sessionID_key)
        # db set offline 
        info = DotDict(tid=tid,
                       login=GATEWAY.TERMINAL_LOGIN.OFFLINE,
                       offline_time=timestamp)
        self.update_terminal_status(info)

        # remind maintenance personnel
        # corp's alert_mobile; zhuhai(liyun.sun, shi.chen, chunfan.yang);
        # beijing:(xiaolei.jia, boliang.guan)

        # 13600335550 三乡, 15919176710 北京测试网
        alert_cid = [13600335550, 15919176710]
        sms_alert_lst = [13417738427]
        email_alert_lst = ['mengxuan.chen@dbjtech.com', 'shi.chen@dbjtech.com', 'qi.liu@dbjtech.com', 'chunfan.yang@dbjtech.com']
        email_alert_lst_cc = ['xiaolei.jia@dbjtech.com']

        #alert_cid = [15901258591, 15919176710]
        #sms_alert_lst = [15901258591,18310505991]
        #email_alert_lst = ['zhaoxia.guo@dbjtech.com']
        #email_alert_lst_cc = ['xiaolei.jia@dbjtech.com']

        alert_info = DotDict(tmobile='',
                             umobile='',
                             corp_name='',
                             offline_cause='',
                             pbat='',
                             offline_time='')
        t = self.db.get("SELECT cid FROM V_TERMINAL WHERE tid = %s LIMIT 1", 
                        tid)
        cid = t.cid if t.get('cid', None) is not None else '0'
        if int(cid) not in alert_cid:
            pass
        else:
            terminal = self.db.get("SELECT mobile, owner_mobile, offline_time, pbat, offline_time"
                                   "  FROM T_TERMINAL_INFO WHERE tid = %s", tid)
            corp = self.db.get("SELECT name, alert_mobile FROM T_CORP WHERE cid = %s", cid)
            sms_alert_lst.append(corp.alert_mobile)

            alert_info.tmobile = terminal.mobile 
            alert_info.umobile = terminal.owner_mobile 
            alert_info.corp_name = corp.name
            alert_info.pbat = terminal.pbat
            offline_time = time.strftime('%Y-%m-%d-%H:%M:%S',time.localtime(terminal.offline_time))
            alert_info.offline_time = offline_time
            alert_info.pbat= terminal.pbat 
            alert_info.offline_cause = u'缺电关机' if terminal.pbat < 5 else u'通讯异常' 

            alert_content = u'尊敬的用户，您好：\n\t移动卫士平台检测到终端离线:（终端号码：%(tmobile)s；车主号码：%(umobile)s；集团名：%(corp_name)s； 离线原因：%(offline_cause)s ； 离线时电量：%(pbat)s；离线时间：%(offline_time)s），请相关人员尽快核查。' 

            alert_content = alert_content % alert_info 

            # send alert-sms
            for mobile in sms_alert_lst:
                SMSHelper.send(mobile, alert_content)

            # send alert-email
            subject = u'移动卫士离线监测'
            EmailHelper.send(email_alert_lst, alert_content, email_alert_lst_cc, files=[], subject=subject) 
            logging.info("[CK] alert_info: %s belongs to special corp: %s, remind associated staff", 
                         alert_info, corp)

    def update_terminal_status(self, info):
        """Update the terminal info according the latest infomation.
        """
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

        # check sim status
        lat, lon = get_latlon_from_cellid(0, 0, 0, 0, terminal_info['mobile'])
        if lat and lon: 
            self.db.execute("UPDATE T_BIND_LOG"
                            "  SET sim_status = 1"
                            "  WHERE tmobile = %s",
                            terminal_info['mobile'])
            logging.info("[CK] tid: %s, mobile: %s heartbeat lost but cellid successed.",
                         info['tid'], terminal_info['mobile'])

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


if __name__ == '__main__':
    ConfHelper.load(options.conf)
    parse_command_line()
    logging.info('come into checkterminalstatus')
    cps = CheckTerminalStatus() 
    #cps.check_terminal_status()
    tid = 'T123SIMULATOR'
    cps.heartbeat_lost_report(tid)
