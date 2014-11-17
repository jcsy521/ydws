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
                u"集团名称", 
                u"车主手机", 
                u"终端手机",
                u"受理时间")

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

OLINE_SHEET = u"在线统计"
OLINE_FILE_NAME = u"在线统计表"
OLINE_HEADER = (u"时间", 
                u"在线数", 
                u"离线数",
                u"定位器总数")

TOTAL_SHEET = u"所有用户统计"
TOTAL_FILE_NAME = u"所有用户统计表"
TOTAL_HEADER_TOP = (u"新增激活终端", 
                    u"流失终端",
                    u"用户登录情况", 
                    u"活跃情况",
                    u"终端情况",
                    u"累计激活终端",
                    u"统计时间")
TOTAL_HEADER = (u"日激活", 
                u"月累计", 
                u"年累计", 
                u"日累计", 
                u"月累计", 
                u"年累计", 
                u"日登录", 
                u"月累计", 
                u"年累计", 
                u"活跃用户", 
                u"沉默用户", 
                u"在线终端", 
                u"离线终端", 
                u"集团用户", 
                u"个人用户", 
                u"年月日")

INDIVIDUAL_SHEET = u"个人用户统计"
INDIVIDUAL_FILE_NAME = u"个人用户统计表"
INDIVIDUAL_HEADER_TOP = (u"新增激活终端", 
                         u"流失终端",
                         u"用户登录情况", 
                         u"活跃情况",
                         u"终端情况",
                         u"统计时间")

INDIVIDUAL_HEADER = (u"日激活", 
                     u"月累计", 
                     u"年累计", 
                     u"日累计", 
                     u"月累计", 
                     u"年累计", 
                     u"日登录", 
                     u"月累计", 
                     u"年累计", 
                     u"活跃用户", 
                     u"沉默用户", 
                     u"在线终端", 
                     u"离线终端", 
                     u"年月日")

ENTERPRISE_SHEET = u"集团用户统计"
ENTERPRISE_FILE_NAME = u"集团用户统计表"
ENTERPRISE_HEADER_TOP = (u"新增激活终端", 
                         u"流失终端",
                         u"新增激活集团",
                         u"用户登录情况", 
                         u"活跃情况",
                         u"终端情况",
                         u"统计时间")
ENTERPRISE_HEADER = (u"日激活", 
                     u"月累计", 
                     u"年累计", 
                     u"日累计", 
                     u"月累计", 
                     u"年累计", 
                     u"日激活", 
                     u"月累计", 
                     u"年累计", 
                     u"日登录", 
                     u"月累计", 
                     u"年累计", 
                     u"活跃用户", 
                     u"沉默用户", 
                     u"在线终端", 
                     u"离线终端", 
                     u"年月日")

OFFLINE_SHEET = u"离线用户统计"
OFFLINE_FILE_NAME = u"离线用户统计表"
OFFLINE_HEADER = (u"用户类型", 
                  u"集团名称", 
                  u"车主号", 
                  u"终端号", 
                  u"sn", 
                  u"版本号", 
                  u"定位器名称", 
                  u"电量", 
                  u"离线时间",
                  u"最近登录时间",
                  u"累计离线时间",
                  u"离线原因",
                  u"备注")


BUSINESS_FILE_NAME = u"用户查询"
BUSINESS_SHEET = u"用户"
BUSINESS_HEADER = (u"序号", 
                   u"集团名称", 
				   u"集团联系人", 
                   u"车主手机", 
                   u"终端手机", 
                   u"sn", 
                   u"版本号", 
                   u"定位器名称", 
                   u"业务类型", 
                   u"在线/离线",
                   u"电量",
                   u"开通时间",
				   u"bt_name",
				   u"bt_mac",)

BINDLOG_FILE_NAME =u"终端绑定记录表"
BINDLOG_SHEET = u"终端绑定"
BINDLOG_HEADER = (u"序号",
                  u"定位手机号",
                  u"操作类型",
                  u"注册时间",
                  u"解绑时间",)

MANUALLOG_FILE_NAME =u"终端设防记录表"
MANUALLOG_SHEET = u"终端设防"
MANUALLOG_HEADER = (u"序号",
                    u"定位手机号",
                    u"操作类型",
                    u"操作时间")



LOCATION_FILE_NAME = u"位置查询表"
LOCATION_SHEET = u"位置查询"
LOCATION_HEADER = (u"序号",
                   u"终端手机号",
                   u"终端序列号",
                   u"加密前纬度",
                   u"加密前经度",
                   u"加密后纬度",
                   u"加密后经度",
                   u"位置描述",
                   u"定位时间",
                   u"定位方式",
                   u"速度（km/h）",
                   u"定位误差(米)",
                   u"基站信息")

OwnerService_FILE_NAME = u"车主服务预登记表"
OwnerService_SHEET = u"预登记车主"
OwnerService_HEADER = (u"序号",
                       u"车主手机号",
                       u"车牌号",
                       u"车型",
                       u"定制时间")


