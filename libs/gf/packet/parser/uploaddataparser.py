# -*- coding: utf-8 -*-

import struct

from constants import GF
from utils.dotdict import DotDict


class UploadDataParser():
    def __init__(self, data):
        self.content = self.parse(data)
        
    def parse(self ,data):
        if not data:
            return
        keys = ['Terminal_id', 'Content_length',]
        content = DotDict()
        start_len = 0
        end_len = 0
        for key in keys:
            length = GF.len[GF.gftype[key]]
            end_len = start_len + length
            value = data[start_len:end_len]
            content[key] = struct.unpack('!' + GF.fmt[GF.gftype[key]], value)[0]
            start_len += length

        data = data[end_len:]
        
        return data
