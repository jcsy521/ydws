# -*- coding: utf-8 -*-

import struct
from hashlib import md5

from constants import GF 
from utils.dotdict import DotDict


class BindParser():
    def __init__(self, data):
        self.gfbody = self.parse(data)
        
    def parse(self, data):
        if not data:
            return
        keys = ['time', 'system_id','md5_code']
        ret = DotDict()
        start_len = 0
        end_len = 0
        for key in keys:
            length = GF.len[GF.gftype[key]]
            end_len = start_len + length
            value = data[start_len:end_len]
            ret[key] = struct.unpack('!' + GF.fmt[GF.gftype[key]], value)[0]
            start_len += length

        return ret

    def get_md5(self, data):
        m = md5()
        m.update(data)
        return m.hexdigest()
        
    def check(self, args):
        success = True
        system_id = '%-16s' % 'pabb' 
        ##########
        args['password'] = 'pabb123'
        ##########
        password = '%-16s' % args['password']
        value = args['time'] + system_id + password
        md5_code = self.get_md5(value).upper()
        if args['md5_code'] != str(md5_code):
            success = False 

        return success
        
class UNBindParser():
    def __init__(self, data):
        self.parse(data)
        
    def parse(self):
        pass
