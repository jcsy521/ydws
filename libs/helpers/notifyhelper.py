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
     chid="2100" 
     apikey="0giz43ztb0" 

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
     msg=msg.replace(" ","")
     ran=str(random.randint(1,100)) 
     m=hashlib.md5() 
     m.update(chid+uid+msg+ran+apikey) 
     hash = m.hexdigest() 
     url = "http://www.push-notification.org/handlers/apns_v1.php?ch=%s&devId=%s&msg=%s&random=%s&hash=%s" % (chid, uid, msg, ran, hash)
     response, content = h.request(url) 
     logging.info("the push url: \n%s,\nthe response: %s", url, content) 

