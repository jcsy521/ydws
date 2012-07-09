# -*- coding: utf-8 -*-

import struct

from constants import GF
from utils.dotdict import DotDict


class SendParser():
    def __init__(self, data):
        self.gfbody = self.parse(data)
        
    def parse(self, data):
        if not data:
            return
        keys = ['Terminal_id', 'Content_length',]
        ret = DotDict()
        start_len = 0
        end_len = 0
        for key in keys:
            length = GF.len[GF.gftype[key]]
            end_len = start_len + length
            value = data[start_len:end_len]
            ret[key] = struct.unpack('!' + GF.fmt[GF.gftype[key]], value)[0]
            start_len += length
        ret['Content'] = data[end_len:]

        return ret

class SendRespParser():
    def __init__(self, data):
        self.gfbody = self.parse(data)
        
    def parse(self, data):
        if not data:
            return
        keys = ['Terminal_id', 'command',]
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
