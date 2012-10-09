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
from helpers.confhelper import ConfHelper

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
        #NOTE: because it's invalid most time, so close it.
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
        data = DotDict(uid=uid,
                       key=key,
                       body=msg)
        response, content = h.request(url, 'POST', body=urlencode(data), headers=headers)
        ret = json_decode(content)
        if ret['status'] == 0:
            logging.info("Push to Android success! Message: %s", ret['message'])
        else:
            logging.error("Push to Android failed! Message: %s", ret['message'])
    
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
    def get_push_key(uid, redis):
        """Get push key of current user for openfie push.
        workflow:
        if push_key in redis:
            return push_key 
        else:
            push_key = push_register()
            keep push_key in redis
        """
        try:
            push_key = redis.getvalue(('push:%s' % uid))
            if not push_key:
                push_key = NotifyHelper.push_register(uid) 
                redis.setvalue(('push:%s' % uid), push_key)
            return push_key
        except Exception as e:
            return None 
            logging.exception("Get push key failed. Exception: %s", e.args)
