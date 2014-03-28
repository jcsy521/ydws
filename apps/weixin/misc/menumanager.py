# -*- coding: utf-8 -*-

import urllib
import json
import urllib2
import sys
import logging

from menus import menu1, menu2, menu3

reload(sys)
sys.setdefaultencoding('UTF-8')


class MenuManager:

    appid = "wx394eee811bd082b1"
    secret = "a1a255d959889b86612cefe39324ef23"
    accessUrl = 'https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=' \
                + appid + '&secret=' + secret
    delMenuUrl = "https://api.weixin.qq.com/cgi-bin/menu/delete?access_token="
    createUrl = "https://api.weixin.qq.com/cgi-bin/menu/create?access_token="
    getMenuUri = "https://api.weixin.qq.com/cgi-bin/menu/get?access_token="

    def getAccessToken(self):
        """
        NOTE: access_token is limited. so you can keep the token when got it, rather than get it every time. 
        """
        f = urllib2.urlopen(self.accessUrl)
        accessT = f.read().decode("utf-8")
        jsonT = json.loads(accessT)
        logging.info("get accesstoken: %s", jsonT)
        return jsonT['access_token']

    def delMenu(self, accessToken):
        html = urllib2.urlopen(self.delMenuUrl + accessToken)
        result = json.loads(html.read().decode("utf-8"))
        logging.info("delete menu. response: %s", result)
        return result["errcode"]

    def createMenu(self, accessToken, menu):
        html = urllib2.urlopen(self.createUrl + accessToken, menu.encode("utf-8"))
        result = json.loads(html.read().decode("utf-8"))
        logging.info("create menu. response: %s", result)
        return result["errcode"]

 
    def getMenu(self, accessToken):
        html = urllib2.urlopen(self.getMenuUri + accessToken)
        print(html.read().decode("utf-8"))

if __name__ == "__main__":
    wx = MenuManager()

    accessToken = wx.getAccessToken()
    wx.delMenu(accessToken)
    wx.createMenu(accessToken, menu3)