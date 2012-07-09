# -*- coding:utf-8 -*-

import struct

from base import BaseComposer


class SendComposer(BaseComposer):
    def __init__(self, data, args):
        self.buf = self.compose(data, args)
        
    def compose(self, data, args):
        # header
        keys = ['Terminal_id', 'Content_length',]
        args['command'] = '0010'
        args['seq'] = '%04d' % int(args['seq'])
                   
        # body
        args['Terminal_id'] = '%-20s' % args['tid']
        args['Content_length'] = '%08d' % len(data)
       
        fmt = '20s8s'
        p_len = 20 + 20 + 8 + len(data)
        args['packet_len'] = '%08d' % p_len
        lst = []
        for key in keys:
            lst.append(str(args[key])) 
        body_buf = struct.pack(fmt, *lst) 
        head_buf = self.pack_headdata(args)
        buf = head_buf + body_buf  

        return buf + data

class SendRespComposer(BaseComposer):
    def __init__(self, args):
        self.buf = self.compose(args)
        
    def compose(self, args):
        args['command'] = '1010'
        args['Terminal_id'] = '%-20s' % args['terminal_id']
        args['type'] = '%-4s' % args['type']

        p_len = 20 + 20 + 4
        args['packet_len'] = '%08d' % p_len
        body_buf = args['Terminal_id'] + args['type'] 
        head_buf = self.pack_headdata(args)
        buf = head_buf + body_buf

        return buf
