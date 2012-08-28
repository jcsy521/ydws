# -*- coding: utf-8 -*-

import logging
import httplib2
import random
import hashlib

from tornado.escape import json_decode, json_encode

from utils.dotdict import DotDict 

def push_to_android(category, uid, tid, location):
     """Push info fo android by the means of ANPS
     """
     h = httplib2.Http()

     secret="324cd0ba0548d36" 
     app_key="e11e7e3e21180fd" 
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
     url = "http://www.android-push.com/api/send/?secret=%s&app_key=%s&client_ids=&alias=%s&msg=%s" % (secret, app_key, alias, msg)
     response, content = h.request(url) 
     logging.info("the push url: \n%s,\nthe response: %s", url, content) 

