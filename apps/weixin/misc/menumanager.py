# -*- coding: utf-8 -*-

import urllib
import json
import urllib2
import sys

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
        f = urllib2.urlopen(self.accessUrl)
        accessT = f.read().decode("utf-8")
        print 'get accesstoken', accessT
        jsonT = json.loads(accessT)
        return jsonT['access_token']

    def delMenu(self, accessToken):
        html = urllib2.urlopen(self.delMenuUrl + accessToken)
        result = json.loads(html.read().decode("utf-8"))
        print 'del menu result', result
        return result["errcode"]

    def createMenu(self, accessToken, menu):
        html = urllib2.urlopen(self.createUrl + accessToken, menu.encode("utf-8"))
        result = json.loads(html.read().decode("utf-8"))
        # print(html.read().decode("utf-8"))
        print(result["errcode"])
        return result["errcode"]

    def getMenu(self, accessToken):
        html = urllib2.urlopen(self.getMenuUri + accessToken)
        print(html.read().decode("utf-8"))


if __name__ == "__main__":
    wx = MenuManager()

    accessToken = wx.getAccessToken()
    print 'menu', menu3
    wx.delMenu(accessToken)

    wx.createMenu(accessToken, menu3)

    #wx.getMenu(accessToken)

    #wx.delMenu(accessToken)

