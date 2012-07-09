# -*- coding: utf-8 -*-

import struct

from constants import GF 
from utils.dotdict import DotDict

class GFCheck(object):
    def __init__(self, response):
        self.heads = []
        self.datas = []
        self.parse_head(response)
        
    def parse_head(self, buf):
        # NOTE: response may include several packets
        # so we'd better parse and split the response with loop
        while True:
            # gf header
            keys = ['packet_len', 'command', 'status', 'seq']
            header = DotDict()
            
            start_len = 0
            end_len = 0
            for key in keys:
                length = GF.len[GF.gftype[key]]
                end_len = start_len + length
                value = buf[start_len:end_len]
                header[key] = struct.unpack('!' + GF.fmt[GF.gftype[key]], value)[0]
                start_len += length

            p_len = int(header['packet_len'])
            data = buf[end_len:p_len]
            self.heads.append(header)
            self.datas.append(data)
            buf = buf[p_len:]
            if not buf:
                break

