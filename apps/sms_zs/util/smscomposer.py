#!/usr/bin/env python
# -*- coding: utf-8 -*-

from string import Template
import base64
import urllib
import os.path
import site
import logging

TOP_DIR_ = os.path.abspath(os.path.join(__file__, "../../../.."))
site.addsitedir(os.path.join(TOP_DIR_, "libs"))
site.addsitedir(os.path.join(TOP_DIR_, "apps/sms_zs"))
from tornado.options import define, options
if 'conf' not in options:
    define('conf', default=os.path.join(TOP_DIR_, "conf/global.conf"))
from helpers.confhelper import ConfHelper

from des import DES
from md5 import MD5
from net.httpclient import HttpClient


class SMSComposer(object):
    
    xml = Template(u"""
                        <r>
                           <id>${id}</id>
                           <q>${q}</q>
                           <m>${m}</m>
                        </r>\r\n
                    """)
    
    def __init__(self, mobile, content):
        ConfHelper.load(options.conf)
        id = ConfHelper.SMS_CONF.id
        s = ConfHelper.SMS_CONF.subport
        q_template = 'id=%s&s=%s&m=%s&p=0&c=%s'
        raw_q = q_template % (id, s, mobile, content)
        logging.info("Raw data : %s", raw_q)
        self.result = None
        try:
            b = base64.encodestring(DES(raw_q).result)
            q = urllib.urlencode({'var' : b})
            q = q[4:]
            mac_key = ConfHelper.SMS_CONF.mac_key
            m = MD5(raw_q + mac_key).result
            self.result = self.xml.safe_substitute(id = id, q = q, m = m)
            
        except Exception as e:
            logging.exception("Package data error, raw data : %s", raw_q)
        
