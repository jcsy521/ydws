#!/bin/bash
# -*- coding:utf-8 -*-

import os.path
import site

TOP_DIR_ = os.path.abspath(os.path.join(__file__, "../../.."))
site.addsitedir(os.path.join(TOP_DIR_, "libs"))


from urllib import urlencode
import httplib2
import logging
import base64
import time
from decimal import Decimal
from utils.public import get_weixin_push_key
from utils.dotdict import DotDict

from tornado.escape import json_encode, json_decode
from tornado.options import define, options, parse_command_line

from helpers.confhelper import ConfHelper
from helpers.queryhelper import QueryHelper


class WeixinPushHelper(object):

    @staticmethod
    def push(tid, body, db, redis): 
        """Push notification to wechat client.
        @tid: terminal tid
        @body: location which  after handle from terminal send,
        @region_id: terminal's region id
        """
        terminal = db.get("SELECT owner_mobile FROM T_TERMINAL_INFO"
                          " WHERE tid = %s",
                          tid)
        owner_mobile = terminal.get('owner_mobile', '')

        user = db.get("SELECT openid FROM T_USER"
                      " WHERE uid = %s",
                      owner_mobile)
        if user:
            openid = user['openid']
        else:
            openid = ''

        if openid:
            h = httplib2.Http()
            t = time.time() * 1000
            key = get_weixin_push_key(openid ,t)
            url = ConfHelper.OPENFIRE_CONF.weixin_url 
            data = DotDict(openid=openid,
                           t=str(t),
                           key=key,
                           packet=body)
            content = {}
            ret = dict(status=-1)
            headers = {"Content-type": "application/json; charset=utf-8"}
            response, content = h.request(url, 'POST', json_encode(data),headers=headers)
            ret = json_decode(content)
            if ret['status'] == 0:
                logging.info("Push to Wechat success! Message: %s, Tid: %s,openid: %s", ret['message'], tid, openid)
            else:
                logging.error("Push to Wechat failed! Message: %s, Tid: %s,openid: %s",ret['message'], tid, openid)
        else:
            logging.info("Push to Wechat: this user donesn't bind Wechat")



if __name__ == '__main__':
    ConfHelper.load('../../conf/global.conf')
    parse_command_line()

