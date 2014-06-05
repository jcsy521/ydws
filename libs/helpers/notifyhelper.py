# -*- coding: utf-8 -*-

import os.path 
DOWNLOAD_DIR_ = os.path.abspath(os.path.join(__file__, "../../../apps/uweb/static/download/"))

from  xml.dom import minidom
import logging
import httplib2
import random
import hashlib
import time
from urllib import urlencode

from tornado.escape import json_decode, json_encode

from utils.dotdict import DotDict 
from utils.misc import safe_utf8, get_ios_id_key, get_ios_badge_key
from helpers.confhelper import ConfHelper
from constants import UWEB 

class NotifyHelper(object):

    @staticmethod
    def get_push_info():
        """Get the app_key, secret and so on from xml. """
        xml = minidom.parse(os.path.join(DOWNLOAD_DIR_,"keys.xml"))
        android = xml.getElementsByTagName('android')
        app_key = android[0].getElementsByTagName('app_key')[0].firstChild.data
        secret = android[0].getElementsByTagName('secret')[0].firstChild.data
        begintime = android[0].getElementsByTagName('begintime')[0].firstChild.data
        endtime = android[0].getElementsByTagName('endtime')[0].firstChild.data
        return DotDict(app_key=app_key,
                       secret=secret,
                       begintime=begintime,
                       endtime=endtime)
    
    @staticmethod
    def push_to_android(category, tid, t_alias, location, push_id, push_key, region_id=None):
        """Push info for android by means of openfire.
        @params:
        category,
        t_alias,
        location,
        push_id,
        push_key,
        """
        # part 1: android-push 
        #NOTE: because it's invalid most time, so close it.
        h = httplib2.Http()
        push_info = NotifyHelper.get_push_info()
        ret = DotDict(tid=tid,
                      category=category,
                      longitude=location.lon,
                      latitude=location.lat,
                      clongitude=location.cLon,
                      clatitude=location.cLat,
                      name=location.name if location.name else '',
                      timestamp=location.timestamp,
                      speed=float(location.speed),
                      degree=float(location.degree),
                      type=location.type,
                      alias=t_alias,
                      pbat=location.pbat,
                      comment=location.comment,
                      # for region
                      region_id=region_id if region_id else -1,)
    
        msg=str(json_encode(ret)) 
        #url = "http://www.android-push.com/api/send/?secret=%s&app_key=%s&client_ids=&alias=%s&msg=%s" % (push_info.secret, push_info.app_key, alias, msg)
        #response, content = h.request(url) 
        #logging.info("the push url: \n%s,\nthe response: %s", url, content) 
    
        ## part 2: openfire push 
        #import subprocess
        #msg_json=json_encode(ret)
        #msg = "curl -d uid=%s -d key=%s -d body='%s' http://drone-003:8005/DbPush/push" % (uid, key, msg_json) 
        #subprocess.call(msg,shell=True)

        headers = {"Content-type": "application/x-www-form-urlencoded; charset=utf-8"}
        url = ConfHelper.OPENFIRE_CONF.push_url 
        data = DotDict(uid=push_id,
                       key=push_key,
                       body=msg)
        response, content = h.request(url, 'POST', body=urlencode(data), headers=headers)
        ret = json_decode(content)
        if ret['status'] == 0:
            logging.info("Push to Android success! Message: %s, Tid: %s, push_id: %s", 
                         ret['message'], tid, push_id)
        else:
            logging.error("Push to Android failed! Message: %s, Tid: %s, push_id: %s", 
                         ret['message'], tid, push_id)
    
    @staticmethod
    def push_register(uid):
        """Create a account for a user in openfire.
        uid: in fact it's owner_mobile.
        """ 
        try:
            h = httplib2.Http()
            msg = DotDict(uid=uid)
            msg={'uid':uid}
            url_create = ConfHelper.OPENFIRE_CONF.accountcreate_url 
            response, content = h.request(url_create, "POST", urlencode(msg),  headers={'Content-Type': 'application/x-www-form-urlencoded'})
            ret = DotDict(json_decode(content))
            if ret.status != 2:
                return ret.key
            else:
                return None
        except Exception as e:
            return None
            logging.exception("Push register failed. Exception: %s", e.args)
    
    @staticmethod
    def get_push_key(push_id, redis):
        """Get push key of current user for openfie push.
        workflow:
        if push_key in redis:
            return push_key 
        else:
            push_key = push_register()
            keep push_key in redis
        """
        try:
            push_key = redis.getvalue(('push:%s' % push_id))
            if not push_key:
                push_key = NotifyHelper.push_register(push_id) 
                redis.setvalue(('push:%s' % push_id), push_key)
            return push_key
        except Exception as e:
            logging.exception("Get push key failed. Exception: %s", e.args)
            return None 

    @staticmethod
    def get_iosbadge(iosid, redis): 
        """Get ios_badge throuth iosid. """ 
        ios_badge = None
        try: 
            ios_badge_key = get_ios_badge_key(iosid) 
            ios_badge = redis.getvalue(ios_badge_key) 
            if ios_badge is not None: 
                ios_badge = int(ios_badge) + 1 
                redis.setvalue(ios_badge_key, ios_badge)
        except Exception as e: 
            logging.exception("Get push key failed. Exception: %s", e.args) 
        finally:
            return ios_badge 

    @staticmethod
    def push_to_ios(category, tid, t_alias, location, ios_id, ios_badge, region_id=None):
        """Push info fo IOS by the means of ANPS
        @param: category,
                tid, 
                t_alias,
                location,
                ios_id,
                ios_bagde
        """

        try:
            h = httplib2.Http()
            
            # 1: format alert 
            CATEGORY = {2:u'电量告警',
                        3:u'震动告警',
                        4:u'移动告警',
                        5:u'SOS',
                        6:u'通讯异常',
                        7:u'进入围栏',
                        8:u'离开围栏',
                        9:u'断电告警' }
            t_alias= t_alias if len(t_alias)<=11 else t_alias[:8]+u'...'
            alert = u"您的定位器 “%s” 产生了%s" % (t_alias, CATEGORY[category])

            # 2: format body 
            ret = DotDict(tid=tid,
                          category=category,
                          longitude=location.lon,
                          latitude=location.lat,
                          clongitude=location.cLon,
                          clatitude=location.cLat,
                          name=location.name if location.name else '',
                          timestamp=location.timestamp,
                          speed=float(location.speed),
                          degree=float(location.degree),
                          type=location.type,
                          alias=t_alias,
                          pbat=location.pbat,
                          comment=location.comment, 
                          region_id=region_id if region_id else -1)

            keys = ['tid',
                    'category', 
                    'latitude', 
                    'longitude', 
                    'clatitude', 
                    'clongitude', 
                    'name', 
                    'timestamp', 
                    'speed', 
                    'degree', 
                    'type', 
                    'alias', 
                    'pbat', 
                    'comment',
                    'region_id']

            def get_body_str(ret):
                body_str = u'' 
                for key in keys:
                    tmp = '#%s' % ret.get(key,'')
                    body_str = safe_utf8(body_str) + safe_utf8(tmp) 
                body_str = body_str[1:]
                return body_str

            body_str = get_body_str(ret)
            #NOTE: here, the maxsize is 180, it bigger than it, set ret.name ''
            if len(body_str) > UWEB.IOS_MAX_SIZE:
                logging.info("Push body is bigger than: %s, set name ''", UWEB.IOS_MAX_SIZE)
                ret.name=''
                body_str = get_body_str(ret)

            headers = {"Content-type": "application/x-www-form-urlencoded; charset=utf-8"}
            url = ConfHelper.OPENFIRE_CONF.ios_push_url 
            data = DotDict(uid=ios_id,
                           alert=safe_utf8(alert),
                           badge=ios_badge,
                           body=safe_utf8(body_str))

            response, content = h.request(url, 'POST', body=urlencode(data), headers=headers)
            if response['status'] == '200':
                ret = json_decode(content)
                if ret['status'] == 0:
                    logging.info("Push to IOS success! Message: %s", ret['message'])
                else:
                    logging.error("Push to IOS failed! Message: %s", ret['message'])
            else:
                logging.error("Push to IOS failed! response: %s", response)

        except Exception as e:
            logging.exception("Push to IOS failed. Exception: %s", e.args)

    @staticmethod
    def check_send_sms(tid):
        flag = 0
        date_dict = dict()
        week_list = list()
        hour = int(time.strftime('%I',time.localtime(time.time())))
        minite = int(time.strftime('%m',time.localtime(time.time()))) 
        nowdate = 3600*hour + 60*minite
        week = int(time.strftime('%w',time.localtime(time.time())))
        if week == 0:
            week = 7
        items = self.db.query("SELECT * FROM T_ALERT_SETTING WHERE tid=%s", tid)
        if items is None:
            return True
        else:
            for item in items:
                date_dict[item["week"]] = [item["start_time"],item["end_time"]]
            for key,date in date_dict.items():
                if key[week] == 1:
                    if data[0] < nowdate and data[1]> nowdate:
                        flag = 1
                        break
            if flag == 1:
                return True
            else:
               return False                   
