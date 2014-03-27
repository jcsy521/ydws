# -*- coding: utf-8 -*-

import hashlib
# import lxml
import time
import os
import urllib2,json
import xml.etree.ElementTree as ET
import commands
import re
import logging

import tornado.web
from tornado.escape import json_decode

from utils.dotdict import DotDict
from base import BaseHandler, authenticated


def checksignature(signature, timestamp, nonce):
    token = "zainaer"
    list = [token, timestamp, nonce]

    list.sort()
    sha1 = hashlib.sha1()
    map(sha1.update, list)
    mysig = sha1.hexdigest()
    return mysig == signature

class WeixinHandler(BaseHandler):

    def get(self):
        signature = self.get_argument('signature', 0)
        timestamp = self.get_argument('timestamp', 0)
        nonce = self.get_argument('nonce', 0)
        echostr = self.get_argument('echostr', 0)
        try:
            if checksignature(signature, timestamp, nonce):
                self.write(echostr)
            else:
                self.write('fail')
        except Exception as e:
            logging.error("[WEIXIN] acquire echostr fail---> %s", echostr)

    def post(self):
        """接收和发送消息(文本消息)
        """
        body = self.request.body
        data = ET.fromstring(body)
        tousername = data.find('ToUserName').text
        fromusername = data.find('FromUserName').text
        createtime = data.find('CreateTime').text
        msgtype = data.find('MsgType').text
        content = data.find('Content').text
        msgid = data.find('MsgId').text

        #  BD#username:password
        bd = re.search('BD#', content)
        f = re.search(':', content)
        if bd:
            username = content[bd.end():f.start()]
            password = content[f.end():]

            cksql = "SELECT　uid FROM T_USER WHERE uid = %s AND password = %s" % (username, password)
            upsql = "UPDATE T_USER SET openid = %s WHERE uid = %s" % (fromusername, username)
            user = self.db.query(cksql)
            if user:
                self.db.query(upsql)
                recontent = u"绑定成功"
             # recontent = ""

        answer = '''<xml>
                <ToUserName><![CDATA[%s]]></ToUserName>
                <FromUserName><![CDATA[%s]]></FromUserName>
                <CreateTime>%s</CreateTime>
                <MsgType><![CDATA[%s]]></MsgType>
                <Content><![CDATA[%s]]></Content>
                </xml>
                '''
        out = answer % (fromusername, tousername, str(int(time.time())), msgtype, recontent)
        self.write(out)
