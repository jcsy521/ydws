# -*- coding: utf-8 -*-

from utils.dotdict import DotDict

# the priority is same with abt
PRIORITY = DotDict(SMS=40, )

SPEED_DIFF = 3 # if speed < 3km/h, be considered as still point.


REALTIME_VALID_INTERVAL = 180000
GPS_REALTIME_INTERVAL = 60000

USER_VALID = DotDict(VALID=1,
                     INVALID=0)

USER_CATEGORY = DotDict(PERSONAL=1,
                        GROUP=0)

LOCATION_TYPE = DotDict(GPS=0,
                        CELLID=1)

LOGIN_WAY=DotDict(WEB=u"web",
                  WAP=u"wap",
                  ANDROID=u"android客户端",
                  IOS=u"ios客户端")

             # you can have up to 10 records in one page
LIMIT=DotDict(PAGE_SIZE=10, 
              TERMINAL=20)

CATEGORY=DotDict(UNKNOWN=0,
                 WEB=10,
                 SMS=11)

CHECK_TERMINAL=DotDict(TID=u'tid',
                       MOBILE=u'mobile')

DEFEND_STATUS=DotDict(NO=0,
                      YES=1)

CELLID_STATUS=DotDict(OFF=0,
                      ON=1)

SERVICE_STATUS=DotDict(OFF=0,
                       ON=1)


TERMINAL_INFO_CATEGORY=DotDict(R=u'r',
                               W=u'w',
                               F=u'f')


TERMINAL_CATEGORY = DotDict(ESPECIAL_GPS_TERMINAL=1,
                            ESPECIAL_NO_GPS_TERMINAL=2, 
                            GENERAL_TERMINAL=3)

EVENT_CATEGORY=DotDict(ILLEGAL_MOVE=1,
                       BEYOND_BOUND=2,
                       POWER_LOW=3,
                       POWER_OFF=4,
                       HEARTBEAT_MISSING=5,
                       SPEED_OVER=6,
                       SHAKE=7)

# the interval of query boundevent, powerevent, track: one week
QUERY_INTERVAL = 7 * 24 * 60 * 60 * 1000

REMOTE_EVENT_COMMAND = DotDict(REBOOT='REBOOT', 
                               LOCK='LOCK')

TERMINAL_PARAMS = DotDict(psw='密码',
                          domain='服务器地址和端口',
                          freq='上报频率',
                          trace='追踪器开关',
                          pulse='心跳时间',
                          phone='报警器sim卡号',
                          owner_mobile='车主号码',
                          radius='围栏告警距离',
                          vib='非法移动告警短信开关',
                          vibl='非法移动告警感应灵敏度',
                          pof='断电和低电告警开关',
                          lbv='低电告警阈值',
                          sleep='节电模式开关',
                          vibgps='GPS过滤功能开关',
                          speed='最大速度',
                          calllock='呼叫防盗器功能设置',
                          calldisp='是否开通来显',
                          vibcall='振动呼叫功能',
                          sms='是否通过短信激活',
                          vibchk='振动告警设置',
                          poft='断电告警功能延搁',
                          wakeupt='自动唤醒延搁',
                          sleept='休眠延搁',
                          acclt='设防延搁',
                          acclock='是否根据acc状态自动设防',
                          stop_service='终端向控制器发起注销动作',
                          cid='预制终端序列号',
                          softversion='软件版本号',
                          gsm='GSM信号强度',
                          gps='GPS卫星编号和强度',
                          vbat='电池电压，充电电压，充电电流',
                          vin='外接电源输入电压',
                          login='是否连接到平台',
                          plcid='控制器序列号',
                          imsi='sim卡的imsi号码',
                          imei='终端设备的imsi号码',)

TERMINAL_UNIT = DotDict(psw='',
                        domain='',
                        freq='s',
                        trace='',
                        pulse='s',
                        phone='',
                        owner_mobile='',
                        radius='m',
                        vib='',
                        vibl='',
                        pof='',
                        lbv='v',
                        sleep='',
                        vibgps='',
                        speed='km/h',
                        calllock='',
                        calldisp='',
                        vibcall='',
                        sms='',
                        vibchk='',
                        poft='s',
                        wakeupt='m',
                        sleept='m',
                        acclt='s',
                        acclock='',
                        stop_service='',
                        cid='',
                        softversion='',
                        gsm='',
                        gps='',
                        vbat='',
                        vin='mv',
                        login='',
                        plcid='',
                        imsi='',
                        imei='',)
