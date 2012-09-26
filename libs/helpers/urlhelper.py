# -*- coding: utf-8 -*-

import logging
import httplib2
from urllib import urlencode

from tornado.escape import json_decode, json_encode

from utils.dotdict import DotDict 

class URLHelper(object):
    
    @staticmethod
    def get_tinyurl(url):
         """Get a tiny url for wap urle.
         """ 
         try:
             h = httplib2.Http()
             msg={'url':url}
             url_create = 'http://dwz.cn/create.php'
             response, content = h.request(url_create, "POST", urlencode(msg),  headers={'Content-Type': 'application/x-www-form-urlencoded'})
             res = DotDict(json_decode(content))
             logging.info("[TINY_URL] response: %s", res) 
             if res.status == 0:
                 return res.tinyurl
             else:
                 return None
         except Exception as e:
             logging.exception("Get tiny url failed. Exception: %s", e.args)
             return None

