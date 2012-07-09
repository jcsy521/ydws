# -*- coding:utf-8 -*-

from base import BaseComposer


class ActiveTestComposer(BaseComposer):
    def __init__(self, args):
        self.buf = self.compose(args)
        
    def compose(self, args):
        # header
        args['command'] = '0020'
        args['packet_len'] = '00000020'
        body_buf = ''           
        head_buf = self.pack_headdata(args)
        buf = head_buf + body_buf  

        return buf
    
class ActiveTestRespComposer(BaseComposer):
    def __init__(self, args):
        self.buf = self.compose(args)
        
    def compose(self, args):
        # header
        args['command'] = '1020'
        args['packet_len'] = '00000020'
        body_buf = ''           
        head_buf = self.pack_headdata(args)
        buf = head_buf + body_buf  

        return buf
    
