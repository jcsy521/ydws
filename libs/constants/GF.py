# -*- coding: utf-8 -*-

gftype = dict(packet_len='packet_len',
              command='command',
              status='status',
              seq='seq',
              Terminal_id='Terminal_id',
              Content_length='Content_length',
              time='time',
              system_id='system_id',
              md5_code='md5_code')

len = dict(packet_len=8,
           command=4,
           status=4,
           seq=4,
           Terminal_id=20,
           Content_length=8,
           time=14,
           system_id=16,
           md5_code=32)

fmt = dict(packet_len='8s',
           command='4s',
           status='4s',
           seq='4s',
           Terminal_id='20s',
           Content_length='8s',
           time='14s',
           system_id='16s',
           md5_code='32s')

