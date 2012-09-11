# -*- coding: utf-8 -*-

import os.path 
DOWNLOAD_DIR_ = os.path.abspath(os.path.join(__file__, "../../../apps/uweb/static/download/"))

from  xml.dom import minidom
import logging
import httplib2
import random
import hashlib
from urllib import urlencode

from tornado.escape import json_decode, json_encode

from utils.dotdict import DotDict 


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
    def push_to_android(category, uid, tid, t_alias, location, key):
         """Push info fo android by the means of ANPS
         """
    
         # part 1: android-push
         h = httplib2.Http()
         push_info = NotifyHelper.get_push_info()
         alias=uid
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
                       alias=t_alias)
    
         msg=str(json_encode(ret)) 
         url = "http://www.android-push.com/api/send/?secret=%s&app_key=%s&client_ids=&alias=%s&msg=%s" % (push_info.secret, push_info.app_key, alias, msg)
         response, content = h.request(url) 
         logging.info("the push url: \n%s,\nthe response: %s", url, content) 
    
         # part 2: curl get
         import subprocess
         msg_json=json_encode(ret)
         msg = "curl -d uid=%s -d key=%s -d body='%s' http://219.131.223.238:8888/DbjPush/push" % (uid, key, msg_json) 
         subprocess.call(msg,shell=True)
    
    @staticmethod
    def push_register(uid):
         """uid: in fact it's mobile.
         """ 
         h = httplib2.Http()
         JSON_HEADER = {"Content-Type": "application/json; charset=utf-8"}
         msg = DotDict(uid=uid)
         msg={'uid':uid}
         url_create = 'http://219.131.223.238:8888/DbjPush/accountCreate'
         response, content = h.request(url_create, "POST", urlencode(msg),  headers={'Content-Type': 'application/x-www-form-urlencoded'})
         res = DotDict(json_decode(content))
         if res.status != 2:
             return res.key
         else:
             return None
    
    @staticmethod
    def get_push_key(uid, redis):
        push_key = redis.getvalue(('push:%s' % uid))
        push_key = None
        if not push_key:
            push_key = NotifyHelper.push_register(uid) 
            redis.setvalue(('push:%s' % uid), push_key)
        return push_key
