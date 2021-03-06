# -*- coding: utf-8 -*-

import urllib
import json
import urllib2
import sys
import logging

import os.path
import site

TOP_DIR_ = os.path.abspath(os.path.join(__file__, "../../../.."))
site.addsitedir(os.path.join(TOP_DIR_, "libs"))
#define('conf', default=os.path.join(TOP_DIR_, "conf/global.conf"))

from helpers.confhelper import ConfHelper

#from db_.mysql import DBConnection
from utils.myredis import MyRedis

from menus import menu1, menu2, menu3

reload(sys)
sys.setdefaultencoding('UTF-8')


class MenuManager:

    appid = "wx394eee811bd082b1"
    secret = "a1a255d959889b86612cefe39324ef23"

    URL = dict(accessUrl = "https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=%s&secret=%s" % (appid, secret), 

               delMenuUrl = "https://api.weixin.qq.com/cgi-bin/menu/delete?access_token=",
               createUrl = "https://api.weixin.qq.com/cgi-bin/menu/create?access_token=",
               getMenuUri = "https://api.weixin.qq.com/cgi-bin/menu/get?access_token=",

               send_msg = "https://api.weixin.qq.com/cgi-bin/message/custom/send?access_token=",

               create_group = "https://api.weixin.qq.com/cgi-bin/groups/create?access_token=%(access_token)s",
               groups = "https://api.weixin.qq.com/cgi-bin/groups/get?access_token=%(access_token)s",

               users="https://api.weixin.qq.com/cgi-bin/user/get?access_token=%(access_token)s&next_openid=",
               get_user_info="https://api.weixin.qq.com/cgi-bin/user/info?access_token=%(access_token)s&openid=%(openid)s&lang=zh_CN",
               
               auth="https://open.weixin.qq.com/connect/oauth2/authorize?appid=wx394eee811bd082b1&redirect_uri=REDIRECT_URI&response_type=code&scope=snsapi_base&state=STATE#wechat_redirect")

    def __init__(self):
        pass
        #self.db = DBConnection().db
        #self.redis = MyRedis()

    def getAccessToken(self):
        """Get access token.
        NOTE: access_token is limited. so you can keep the token when got it, rather than get it every time. 
        """

        token = None
        #self.redis.set('token', token)
        #token = self.redis.get('token')
        if not token:
            f = urllib2.urlopen(self.URL['accessUrl'])
            accessT = f.read().decode("utf-8")
            jsonT = json.loads(accessT)
            logging.info("get accesstoken: %s", jsonT)
            token = jsonT['access_token']
            #self.redis.set('token', token)
            logging.info("generate a new token: %s, and keep it.", token)

        return token 

    def delMenu(self, accessToken):
        """Delete existed menu.
        """
        html = urllib2.urlopen(self.delMenuUrl + accessToken)
        result = json.loads(html.read().decode("utf-8"))
        logging.info("delete menu. response: %s", result)
        return result["errcode"]

    def createMenu(self, accessToken, menu):
        """Create a menu according json.
        """
        html = urllib2.urlopen(self.URL['createUrl'] + accessToken, menu.encode("utf-8"))
        result = json.loads(html.read().decode("utf-8"))
        logging.info("create menu. response: %s", result)
        return result["errcode"]
 
    def getMenu(self, accessToken):
        html = urllib2.urlopen(self.URL['getMenuUri'] + accessToken)
        print html.read().decode("utf-8")

    def send_msg(self, access_token):
        body= """
        {
          "touser":"oPaxZt3o-PdbYCLKagXuOCoCJG5Y",
          "msgtype":"text",
          "text":
          {
               "content":"Hello World"
          }
        }
        """ 
        html = urllib2.urlopen(self.URL['send_msg'] + access_token, body)
        print html.read().decode("utf-8")

    def get_user_info(self, accessToken, openid):
        data = dict(access_token=accessToken,
                    openid=openid) 
        html = urllib2.urlopen(self.URL['get_user_info'] % data)
        print html.read().decode("utf-8")

    def create_group(self, access_token):
        body= """
        {
           "group": {
               "id": 107, 
               "name": "test"
           }
        }
        """ 
        data = dict(access_token=access_token) 
        html = urllib2.urlopen(self.URL['create_group'] % data, body)
        print html.read().decode("utf-8")

    def groups(self, access_token):
        """ 
        """
        data = dict(access_token=access_token) 
        html = urllib2.urlopen(self.URL['groups'] % data)
        print html.read().decode("utf-8")

    def users(self, access_token):
        """ 
        """
        data = dict(access_token=access_token) 
        html = urllib2.urlopen(self.URL['users'] % data)
        print html.read().decode("utf-8")

    def auth(self):
        """ 
        """
        url = 'http://www.ichebao.net'
     
        data = dict(redirect_uri=url)
        auth_url = urllib.urlencode(data)
        scope = 'snsapi_base'
        #scope = 'snsapi_userinfo'
        state = '123'
  
        data = dict(appid=self.appid,
                    auth_url=auth_url,
                    scope=scope,
                    state=state) 
        full_path = self.URL['auth'] % data
        html = urllib2.urlopen(full_path)
        print html.read()


if __name__ == "__main__":
    wx = MenuManager()
    accessToken = wx.getAccessToken()
    #wx.delMenu(accessToken)
    wx.createMenu(accessToken, menu3)
    wx.getMenu(accessToken)
    #wx.send_msg(accessToken)
    # wx.get_user_info(accessToken, "oPaxZt3o-PdbYCLKagXuOCoCJG5Y")
    # wx.create_group(accessToken )
    #wx.groups(accessToken )
    #wx.users(accessToken )
    #wx.auth()
