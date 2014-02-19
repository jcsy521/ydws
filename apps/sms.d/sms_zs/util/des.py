#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os.path
import site
from pyDes import *
import struct
TOP_DIR_ = os.path.abspath(os.path.join(__file__, "../../../.."))
site.addsitedir(os.path.join(TOP_DIR_, "libs"))
from tornado.options import define, options
if 'conf' not in options:
    define('conf', default=os.path.join(TOP_DIR_, "conf/global.conf"))
from helpers.confhelper import ConfHelper
from utils.misc import safe_utf8

class DES(object):
    
    def __init__(self, data):
        ConfHelper.load(options.conf)
        data = safe_utf8(data)
        length = str(len(data))
        bytes = struct.pack(length + 's', data)
        des_key = ConfHelper.SMS_CONF.des_key
        k = des(des_key, CBC, des_key, pad=None, padmode=PAD_PKCS5)
        self.result = k.encrypt(bytes)
        
