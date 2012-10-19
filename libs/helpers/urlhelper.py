# -*- coding: utf-8 -*-

import logging
import httplib2
from urllib import urlencode
import hashlib
import random

from tornado.escape import json_decode, json_encode

from utils.dotdict import DotDict 

class URLHelper(object):
    
    @staticmethod
    def get_tinyurl(url):
        """Get a tiny url for wap url.
        """ 
        try:
            # Baidu dwz
            #h = httplib2.Http()
            #msg={'url':url}
            #url_create = 'http://dwz.cn/create.php'
            #response, content = h.request(url_create, "POST", urlencode(msg),  headers={'Content-Type': 'application/x-www-form-urlencoded'})
            #res = DotDict(json_decode(content))
            #logging.info("[TINY_URL] response: %s", res) 
            #if res.status == 0:
            #    return res.tinyurl
            #else:
            #    return None

            # google
            h = httplib2.Http()
            url_create = 'https://www.googleapis.com/urlshortener/v1/url'
            msg = json_encode({'longUrl': url})
            response, content = h.request(url_create,
                                          "POST",
                                          msg,
                                          headers = {'Content-Type': 'application/json'})
            res = DotDict(json_decode(content))
            logging.info("[TINY_URL] response: %s", res) 
            return res.get('id', None)

        except Exception as e:
            logging.exception("Get tiny url failed. Exception: %s", e.args)
            return None

    @staticmethod
    def get_tinyid(url):
        """get a tiny id contains 6 chars"""
        try:
            # acb tinyid for tinyurl
            seed = "abcdefghijklmnopqrstuvwxyz0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            hexnum = hashlib.md5(url).hexdigest()
            hexLen = len(hexnum)
            subHexLen = hexLen / 8
            output = []

            for i in xrange(0, subHexLen):
                subHex = hexnum[i*8:i*8+8]
                subHex = 0x3FFFFFFF&int(1*('0x%s'%subHex), 16)
                suboutput = []
                for n in xrange(0, 6):
                    index = 0x0000003D & subHex
                    suboutput.append(seed[int(index)])
                    subHex = subHex >> 5
                output.append(''.join(suboutput))

            tinyid = output[random.randrange(0, 4)]
            logging.info("[TINY_URL] tinyid: %s", tinyid)

            return tinyid
        except Exception as e:
            logging.exception("Get tiny id failed. Exception: %s", e.args)
            return None
