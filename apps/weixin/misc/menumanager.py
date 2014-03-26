# -*- coding: utf-8 -*-

import urllib
import json
import urllib2
import sys
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
        jsonT = json.loads(accessT)
        return jsonT['access_token']

    def delMenu(self, accessToken):
        html = urllib2.urlopen(self.delMenuUrl + accessToken)
        result = json.loads(html.read().decode("utf-8"))
        return result["errcode"]

    def createMenu(self, accessToken):
        menu ='''
       {
            "button":[
            {
               "name":"车辆",
               "sub_button":[
               {
                   "type":"click",
                   "name":"车辆列表",
                   "key":"v100_BUSLIST"
               },
               {
                   "type":"click",
                   "name":"车辆切换",
                   "key":"v100_BUSCHANGE"
               },
               {
                   "type":"click",
                   "name":"实时定位",
                   "key":"v100_RTL"
               },
               {
                   "type":"click",
                   "name":"查询警告",
                   "key":"v100_BUSWARING"
               }]
            },
            {
                "name":"设防撤防",
                "sub_button":[
                {
                   "type":"click",
                   "name":"设防",
                   "key":"v100_fortify"
                },
                {
                   "type":"click",
                   "name":"撤防",
                   "key":"v100_withdraw"
                }]
            },
            {
                "name":"工具",
                "sub_button":[
                {
                   "type":"click",
                   "name":"帐号绑定",
                   "key":"v100_bound"
                },
                {
                    "type":"click",
                    "name":"解绑帐号",
                    "key":"v100_unbound"
                },
                {
                    "type":"view",
                    "name":"最新资讯",
                    "url":"http://www.soso.com/"
                },
                {
                    "type":"view",
                    "name":"操作指南",
                    "url":"http://www.soso.com/"
                }
                ]
            }]
        }'''

        menu2 = '''
       {
            "button":[
            {
                "type":"view",
                "name":"车辆列表",
                "url":"http://www.soso.com/"
            },
            {
                "type":"view",
                "name":"查询警告",
                "url":"http://www.soso.com/"
            },
            {
                "name":"账户管理",
                "sub_button":[
                {
                   "type":"click",
                   "name":"设防",
                   "key":"v100_fortify"
                },
                {
                   "type":"click",
                   "name":"撤防",
                   "key":"v100_withdraw"
                }]

            }]
        }
        '''

        html = urllib2.urlopen(self.createUrl + accessToken, menu2.encode("utf-8"))
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
    wx.createMenu(accessToken)
    wx.getMenu(accessToken)


