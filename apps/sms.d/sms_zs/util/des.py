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

class DES(object):
    
    def __init__(self, data):
#        print " data type : ", type(data)
        ConfHelper.load(options.conf)
        data = data.encode('utf-8')
        length = str(len(data))
        bytes = struct.pack(length + 's',data)
        des_key = ConfHelper.SMS_CONF.des_key
        k = des(des_key, CBC, des_key, pad=None, padmode=PAD_PKCS5)
        self.result = k.encrypt(bytes)

#        print "Encrypted: %r" % self.result
#        print "Decrypted: %r" % k.decrypt(self.result)
#        assert k.decrypt(self.result, padmode=PAD_PKCS5) == data
        
        
