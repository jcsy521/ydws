#~/bin/python
#encoding:utf-8

import sys
import os.path
import site
import time
import tornado

TOP_DIR_ = os.path.abspath(os.path.join(__file__, "../../../"))
site.addsitedir(os.path.join(TOP_DIR_, "libs"))

import logging
from tornado.options import define, options, parse_command_line

from db_.mysql import DBConnection
from utils.myredis import MyRedis
from utils.dotdict import DotDict
from utils.public import get_push_key

from helpers.confhelper import ConfHelper
from helpers.queryhelper import QueryHelper
from helpers.wspushhelper import WSPushHelper
from helpers.emailhelper import EmailHelper
from helpers.smshelper import SMSHelper


class Test(object):

    def __init__(self):
        self.db = DBConnection().db
        self.redis = MyRedis()

class WsPush(Test):

    def __init__(self, tid):
        # call the init of further.
        super(WsPush, self).__init__()
        self.tid = tid
        self.uid = QueryHelper.get_uid_by_tid(self.tid, self.db)

    def register(self):
        start_time = time.time()
        t = int(time.time()) * 1000
        push_key = get_push_key(self.uid, t)
        res = WSPushHelper.register(self.uid, t, push_key, self.redis)
        end_time = time.time()
        print "register time used: %s" % (end_time - start_time)
        print res
        return res

    def push(self, packet):
        start_time = time.time()
        t = int(time.time()) * 1000
        t_info = QueryHelper.get_terminal_basic_info(self.tid, self.db)
        uid = t_info.get('umobile','')
        cid = t_info.get('cid','') 
        lst = [] 

        if uid: 
            lst.append(uid) 
        if cid: 
            lst.append(cid) 

        for item in set(lst):
            push_key = get_push_key(item, t)
            res = WSPushHelper.push(item, t, push_key, packet, self.redis, badge="")
            end_time = time.time()
            #print "push time: %s" % (end_time - start_time)
            #print res

        print "push time used: %s" % (end_time - start_time)
        return res

    def pushS3(self, category):
        """
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
        corp = self.db.get("SELECT * FROM V_TERMINAL where tid = %s",
                            self.tid) 
        if corp:
            groups = self.db.query("select * from T_GROUP where corp_id = %s",
                                   corp['cid'])
            for group in groups:
                terminals = self.db.query("SELECT * FROM T_TERMINAL_INFO"
                                          "  WHERE group_id = %s "
                                          "  AND service_status= 1", # only success
                                          group['id'])
                #TODO: list
                res.append(dict(group_id=group['id'],
                                group_name=group['name'],
                                tids=[terminal['tid'] for terminal in terminals]
                                ))
        else:
            res = []
        packet = dict(packet_type="S3",
                      res=res)
        res = self.push(packet)
        #print "pushS3: %s" % res
        return res

    def pushS4(self, op):
        """
        res = []
        res.append(dict(tid='tid1',
                        login_status=1))
        res.append(dict(tid='tid2',
                        login_status=2))
        """

        res = [] 
        corp = self.db.get("SELECT * FROM V_TERMINAL where tid = %s",
                            self.tid) 
        if corp:
            terminals = self.db.query("SELECT tid FROM V_TERMINAL WHERE cid= %s",
                                      corp['cid'])
            for terminal in terminals:
                t = QueryHelper.get_terminal_info(terminal['tid'], self.db, self.redis) 
                res.append(dict(tid=terminal['tid'],
                                biz_type=0,
                                login_status=t['login']))
        else:
            res = []

        packet = dict(packet_type="S4",
                      res=res)
        res = self.push(packet)

        return res

    def pushS5(self, status):
        """
        """
        res = []
        res.append(dict(tid=self.tid,
                        biz_type=0,
                        #alias='123123',
                        alias=u'6891日璐终端',
                        regin_id=123,
                        category=3, 
                        pbat=100,
                        locate_status=1,
                        #timestamp=1410939622,
                        timestamp=int(time.time()),
                        longitude=419004000,
                        latitude=143676000,
                        clongitude=419004000,
                        clatitude=143676000,
                        address='name',
                        speed=111,
                        degree=203,
                        gsm=0,
                        locate_error=100,
                        gps=25,
                    ))

        packet = dict(packet_type="S5",
                      res=res)
        res = self.push(packet)
        #print "pushS5: %s" % res
        return res

    def pushS6(self):
        res = []
        res.append(dict(tid=self.tid,
                        biz_type=0,
                        gps=24,
                        gsm=9,
                        pbat=43,
                        ))
        packet = dict(packet_type="S6",
                      res=res)
        res = self.push(packet)
        #print "pushS6: %s" % res
        return res

    def pushS7(self):
        res = []
        res.append(dict(tid=self.tid,
                        biz_type=0,
                        alias='alias',
                        icon_type=1,
                        owner_mobile='13011292217',
                        ))

        packet = dict(packet_type="S7",
                      res=res)
        res = self.push(packet)
        #print "pushS7: %s" % res
        return res

    def pushS8(self):
        res = []
        res.append(dict(tid=self.tid,
                        biz_type=0,
                        acc_message=1,
                        ))

        packet = dict(packet_type="S8",
                      res=res)
        res = self.push(packet)
        #print "pushS7: %s" % res
        return res


#mobiles = ["18310505991"]
mobiles = ["13693675352","18310505991",'13425788834']

def send(content, mobile):
    logging.info("Send %s to %s", content, mobile)
    #NOTE: send encrypt sms to mobile
    response = SMSHelper.send(mobile, content)
    #NOTE: send general sms to mobile
    #response = SMSHelper.send(mobile, content)
    logging.info("Response: %s", response)

def send_sms():
    # test 

    print '[wspush-checer] wspush failed'
    return

    redis = MyRedis()
    key = 'wspush_alarm'
    interval = 60*5 # 5 minutes
    alarm_flag = redis.get(key)
    if alarm_flag:
        print '[wspush-checer] do not send alarm again in %(interval)s(seconds)' % locals()  
        return

    url=ConfHelper.UWEB_CONF.url_out
    content = u'WSPush 服务异常，请及时查看。url:%s' % url
    for mobile in mobiles:
        send(content, mobile)
        redis.setvalue(key, True, interval)
        print '[wspush-checer] send alarm sms to %(mobile)s' % locals()

def test_wspush():

    try:
        # jiaxiaolei
        #tid = 'T123SIMULATOR'
        tid = 'B123SIMULATOR'

        ps = WsPush(tid)
        res = ps.register()
        print '[wspush-checer] register res', res
        if (not res) or (res['status_code'] != 200):
            send_sms()

        ##res = ps.pushS3(5)
        #print '[wspush-checer] s3 res', res
        #if (not res) or (res['status_code'] != 200):
        #    send_sms()

        ps.pushS4(1)

        ps.pushS5(1)
        #ps.pushS6()
        #ps.pushS7()
        #ps.pushS8()
    except Exception as e:
        logging.exception('[wspush-checer] test_wspush excepton. Exception:%s' % e.args)
        #print '[wspush-checer] test_wspush excepton. Exception:%s' % e.args 
        send_sms()

def main():

    while True:
        test_wspush()
        time.sleep(30)

if __name__ == "__main__":
    tornado.options.parse_command_line()
    ConfHelper.load(os.path.join(TOP_DIR_, "conf/global.conf"))


    main()
