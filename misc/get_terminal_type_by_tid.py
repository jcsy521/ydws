# -*- coding: utf-8 -*-

import sys
import os.path
from tornado.options import define, options, parse_command_line

define('tid', default="")

# global definition
# base = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, A, B, C, D, E, F]
base = [str(x) for x in range(10)] + [ chr(x) for x in range(ord('A'),ord('A')+6)]

# hex2dec
# 十六进制 to 十进制
def hex2dec(string_num):
    return str(int(string_num.upper(), 16))

# dec2bin
# 十进制 to 二进制: bin() 
def dec2bin(string_num):
    num = int(string_num)
    mid = []
    while True:
        if num == 0: break
        num,rem = divmod(num, 2)
        mid.append(base[rem])

    return ''.join([str(x) for x in mid[::-1]])

# hex2tobin
# 十六进制 to 二进制: bin(int(str,16)) 
def hex2bin(string_num):
    return dec2bin(hex2dec(string_num.upper()))

def usage():
    print "Usage: python get_terminal_type_by_tid.py --tid=[tid]"

def main():
    parse_command_line()
    if not 'tid' in options:
        usage()
        exit(1)

    tid = options.tid
    
    bin_tid = hex2bin(tid)
    
    l = 40 - len(bin_tid)
    s = '0' * l

    sn= s + bin_tid

    print 'bin SN:', sn 
    ttype = sn[15:18]
    if ttype == "000":
        print 'ZJ100'
    elif ttype == '001':
        print 'ZJ200'
    else:
        print 'Unknow terminal type'

if __name__ == "__main__":
    main()
