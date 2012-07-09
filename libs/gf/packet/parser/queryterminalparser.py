# -*- coding: utf-8 -*-

import struct

from constants import GF 
from utils.dotdict import DotDict


class QueryTerminalParser():
    def __init__(self, data):
        self.vgdata = self.parse(data)
        
    def parse(self ,data):
        if not data:
            return
        keys = ['Terminal_count', 'Terminal_id',]
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
