# -*- coding:utf-8 -*-

import struct


class BaseComposer(object):
    
    def pack_headdata(self, args):
        keys = ['packet_len', 'command', 'status', 'seq']
        
        args['status'] = args.get('status') if args.get('status') else '0000'
        fmt = '!8s4s4s4s'
        lst = []
        
        for key in keys:
            lst.append(args.get(key))
        head_buf = struct.pack(fmt, *lst)
        return head_buf
