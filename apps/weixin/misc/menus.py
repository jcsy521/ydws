# -*- coding: utf-8 -*-

menu1 ='''
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

menu3 = '''
       {
         "button":[
            {
                "type":"view",
                "name":"车辆列表",
                "url":"https://open.weixin.qq.com/connect/oauth2/authorize?appid=wx394eee811bd082b1&redirect_uri=http://weixin.ichebao.net/terminals&response_type=code&scope=snsapi_base&state=STATE#wechat_redirect"
            },
            {
                "type":"view",
                "name":"查询警告",
                "url":"https://open.weixin.qq.com/connect/oauth2/authorize?appid=wx394eee811bd082b1&redirect_uri=http://weixin.ichebao.net/event&response_type=code&scope=snsapi_base&state=STATE#wechat_redirect"
            },
            {
                "name":"账户管理",
                "sub_button":[
                  {
                     "type":"view",
                     "name":"绑定",
                     "url":"https://open.weixin.qq.com/connect/oauth2/authorize?appid=wx394eee811bd082b1&redirect_uri=http://weixin.ichebao.net/bind&response_type=code&scope=snsapi_base&state=STATE#wechat_redirect"
                  },
                  {
                     "type":"view",
                     "name":"解绑",
                     "url":"https://open.weixin.qq.com/connect/oauth2/authorize?appid=wx394eee811bd082b1&redirect_uri=http://weixin.ichebao.net/unbind&response_type=code&scope=snsapi_base&state=STATE#wechat_redirect"
                  }
                  
               ]
            }
          ]
        }
        '''
