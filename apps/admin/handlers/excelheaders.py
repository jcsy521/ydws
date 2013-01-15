# -*- coding: utf-8 -*-

# excel headers for different queries.

BUSSINESS_FILE_NAME = u'个人用户查询'
BUSSINESS_SHEET = u'用户信息'
BUSSINESS_HEADER = (u"车主姓名", 
                    u"车主手机", 
                    u"终端手机",
                    u"车牌号",
                    u"受理状态") 

ECBUSINESS_FILE_NAME = u'集团用户查询'
ECBUSINESS_SHEET = u'用户信息'
ECBUSINESS_HEADER = (u"车主姓名", 
                     u"车主手机", 
                     u"终端手机",
                     u"车牌号",
                     u"受理状态") 

SUBSCRIBER_SHEET = u"地市用户统计"
SUBSCRIBER_FILE_NAME = u"地市用户统计"
SUBSCRIBER_HEADER = (u"序号",
                     u"集团总数", 
                     u"终端总数") 

ECSUBSCRIBER_FILE_NAME = u'集团用户统计'
ECSUBSCRIBER_SHEET = u'集团用户统计'
ECSUBSCRIBER_HEADER = (u"序号",
                       u"集团名称", 
                       u"终端总数") 

DAILY_SHEET = u"日报"
DAILY_FILE_NAME = u"业务日报"
DAILY_HEADER = (u"序号", 
                u"新增集团数", 
                u"集团到达数", 
                u"新增终端数",
                u"终端到达数")

MONTHLY_FILE_NAME = u"业务月报"
MONTHLY_SHEET = u"月报"
MONTHLY_HEADER = (u"序号", 
                  u"新增集团数", 
                  u"集团到达数", 
                  u"新增终端数",
                  u"终端到达数")

YEARLY_FILE_NAME = u"业务年报"
YEARLY_SHEET = u"年报"
YEARLY_HEADER = (u"序号", 
                 u"新增集团数", 
                 u"集团到达数", 
                 u"新增终端数",
                 u"终端到达数")
