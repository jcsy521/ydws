# -*- coding: utf-8 -*-

import os.path 
DOWNLOAD_DIR_ = os.path.abspath(os.path.join(__file__, "../../../apps/uweb/static/download/"))

from  xml.dom import minidom
import logging
import httplib2
import random
import hashlib

from tornado.escape import json_decode, json_encode

from utils.dotdict import DotDict 

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

def push_to_android(category, uid, tid, location):
     """Push info fo android by the means of ANPS
     """

     h = httplib2.Http()
     push_info = get_push_info()
     alias=uid

     ret = DotDict(category=category,
                   tid=tid,
                   uid=uid,
                   clongitude=location.cLon,
                   clatitude=location.cLat,
                   timestamp=location.timestamp,
                   name=location.name,
                   volume=location.pbat,
                   speed=location.speed,
                   type=location.type)

     msg=str(json_encode(ret)) 
     url = "http://www.android-push.com/api/send/?secret=%s&app_key=%s&client_ids=&alias=%s&msg=%s" % (push_info.secret, push_info.app_key, alias, msg)
     response, content = h.request(url) 
     logging.info("the push url: \n%s,\nthe response: %s", url, content) 

