#!/usr/bin/env python
# -*- coding: utf-8 -*-

import hashlib
from utils.misc import safe_utf8

class MD5(object):
    
    def __init__(self, str):
        hash_object = hashlib.md5()
        hash_object.update(safe_utf8(str))
        self.result = hash_object.hexdigest()
        
        
