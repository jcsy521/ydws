# -*- coding:utf-8 -*-

import struct

from base import BaseComposer


class UploadDataComposer(BaseComposer):
    def __init__(self, args):
        self.buf = self.compose(args)
        
    def compose(self, args):
        # header
        keys = ['Terminal_id', 'Content_length',]
        args['command'] = '0011'
        args['seq'] = '%04d' % int(args['seq'])
                   
        # body
        args['Terminal_id'] = '%-20s' % args['dev_id']
        args['Content_length'] = '%08d' % len(args['content'])
       
        fmt = '20s8s'
        p_len = 20 + 20 + 8 + len(args['content'])
        args['packet_len'] = '%08d' % p_len
        lst = []
        for key in keys:
            lst.append(str(args[key])) 
        body_buf = struct.pack(fmt, *lst) 
        head_buf = self.pack_headdata(args)
        buf = head_buf + body_buf + args['content'] 

        return buf

class UploadDataRespComposer(BaseComposer):
    def __init__(self, args):
        self.buf = self.compose(args)
        
    def compose(self, args):
        # header
        args['command'] = '1011'
        args['packet_len'] = '00000020'
        body_buf = ''           
        head_buf = self.pack_headdata(args)
        buf = head_buf + body_buf  

        return buf
