# -*- coding:utf-8 -*-

import struct
from hashlib import md5

from base import BaseComposer
       
        
class BindComposer(BaseComposer):
    def __init__(self, args):
        self.buf = self.compose(args)
    
    def get_md5(self, data):
        m = md5()
        m.update(data)
        return m.hexdigest()

    def compose(self, args):
        # header
        args['packet_len'] = '00000082'
        args['command'] = '0001'
        args['status'] = '0000'
            
        # body
        keys = ['time', 'system_id', 'md5_code']
        args['system_id'] = '%-16s' % args['username']
        args['password'] = '%-16s' % args['password']
        value = args['time'] + args['system_id'] + args['password']
        args['md5_code'] = self.get_md5(value).upper()
        fmt = '14s16s32s'
        lst = []
        for key in keys: 
            lst.append(args[key])
        body_buf = struct.pack(fmt, *lst) 
        head_buf = self.pack_headdata(args)
        buf = head_buf + body_buf        

        return buf
    
class BindRespComposer(BaseComposer):
    def __init__(self, args):
        self.buf = self.compose(args)
        
    def compose(self, args):
        # header
        args['command'] = '1001'
        args['packet_len'] = '00000020'
        body_buf = ''           
        head_buf = self.pack_headdata(args)
        buf = head_buf + body_buf  

        return buf
    
class UNBindComposer(BaseComposer):
    def __init__(self, args):
        self.buf = self.compose(args)
    
    def compose(self, args):
        # header
        args['packet_len'] = '00000020'
        args['command'] = '0002'
        args['status'] = '0000'
             
        buf = self.pack_headdata(args)
               
        return buf

class UNBindRespComposer(BaseComposer):
    def __init__(self, args):
        self.buf = self.compose(args)
        
    def compose(self, args):
        # header
        args['command'] = '1002'
        args['packet_len'] = '00000020'
        body_buf = ''           
        head_buf = self.pack_headdata(args)
        buf = head_buf + body_buf  

        return buf
