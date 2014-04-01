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
        """Receive and response.
        """
        body = self.request.body
        logging.info("[WEIXIN] post request: %s", body)
        data = ET.fromstring(body)
        tousername = data.find('ToUserName').text
        openid = data.find('FromUserName').text
        createtime = data.find('CreateTime').text
        msgtype = data.find('MsgType').text
        
        out = 'pass'
        answer = '''<xml>
                <ToUserName><![CDATA[%s]]></ToUserName>
                <FromUserName><![CDATA[%s]]></FromUserName>
                <CreateTime>%s</CreateTime>
                <MsgType><![CDATA[%s]]></MsgType>
                <Content><![CDATA[%s]]></Content>
                </xml>
                '''

        if msgtype == 'text':
            content = data.find('Content').text
            content = content.lower()
            msgid = data.find('MsgId').text
            # BD#username:password
            bd = re.search('bd#', content)
            jb = re.search('jb#', content)
            help = re.search('help', content)
            f = re.search(':', content)
            if bd:
                logging.info("[WEIXIN] bd")
                recontent = u"绑定失败"
                username = content[bd.end():f.start()]
                password = content[f.end():]

                cksql = "SELECT uid FROM T_USER WHERE uid = %s AND password = password(%s)" % (username, password)
                upsql = "UPDATE T_USER SET openid = '%s' WHERE uid = %s" % (openid, username)
                user = self.db.query(cksql)
                if user:
                    self.db.execute(upsql)
                    recontent = u"绑定成功"
                    out = answer % (openid, tousername, str(int(time.time())), msgtype, recontent)
            elif jb:
                # JB#username:password
                logging.info("[WEIXIN] jb")
                recontent = u"解绑失败"
                username = content[jb.end():f.start()]
                password = content[f.end():]
                cksql = "SELECT uid FROM T_USER WHERE uid = %s AND password = password(%s)" % (username, password)
                user = self.db.query(cksql)
                if user:
                    self.db.execute("UPDATE T_USER SET openid = '' WHERE uid = %s ",
                                    username)
                    recontent = u"解绑成功"
                else:
                    recontent = u"输入的解绑用户名或密码有误"
                out = answer % (openid, tousername, str(int(time.time())), msgtype, recontent)
            elif help:
                logging.info("[WEIXIN] help")
                recontent = u"1. 绑定：bd#username:password\n2. 解绑：jb#username:password\n3.帮助 help "
                out = answer % (openid, tousername, str(int(time.time())), msgtype, recontent)
            else:
                logging.info("[WEIXIN] help")
                recontent = u"1. 绑定：bd#username:password\n2. 解绑：jb#username:password\n3.帮助 help "
                out = answer % (openid, tousername, str(int(time.time())), msgtype, recontent)
        else:
            pass
        logging.info("[WEIXIN] response: %s", out)
        self.write(out)
