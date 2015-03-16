# -*- coding:utf8 -*-

import time
import os.path
import site
TOP_DIR_ = os.path.abspath(os.path.join(__file__, "../../.."))
site.addsitedir(os.path.join(TOP_DIR_, "libs"))

import logging
from tornado.options import define, options, parse_command_line
from tornado.escape import json_decode, json_encode
from utils.dotdict import DotDict
from helpers.gfsenderhelper import GFSenderHelper
from codes.errorcode import ErrorCode
from helpers.confhelper import ConfHelper


def test():
    status = ErrorCode.SUCCESS
    
    seq = str(int(time.time()*1000))[-4:]
    args = DotDict(seq=seq,
                   tid='jiabind')
    response = GFSenderHelper.forward(GFSenderHelper.URLS.UNBIND, args)
    response = json_decode(response)
    print 'response', response 
    if response['success'] == ErrorCode.SUCCESS:
        logging.info("[ADMIN] Umobile: %s, tid: %s, tmobile:%s GPRS unbind successfully",
                    pmobile, terminal.tid, tmobile)
    else:
        status = response['success']
    print 'status', status


if __name__ == '__main__':
    ConfHelper.load('../../conf/global.conf')
    parse_command_line()
    test()


