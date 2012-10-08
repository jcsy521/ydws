#!/usr/bin/env python
# -*- coding: utf-8 -*-

import hashlib

class MD5(object):
    
    def __init__(self, str):
        hash_object = hashlib.md5()
        hash_object.update(str.encode('utf-8'))
        self.result = hash_object.hexdigest()
        
        
