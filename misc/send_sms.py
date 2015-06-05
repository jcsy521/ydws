# -*- coding: utf-8 -*-

import sys
import os.path
import site
TOP_DIR_ = os.path.abspath(os.path.join(__file__, "../.."))
site.addsitedir(os.path.join(TOP_DIR_, "libs"))
import logging

from tornado.options import define, options, parse_command_line
define('send', default="one")
define('mobile', default="")

from helpers.confhelper import ConfHelper
from helpers.smshelper import SMSHelper
from db_.mysql import DBConnection

def send(content, mobile):
    logging.info("Send %s to %s", content, mobile)
    #NOTE: send encrypt sms to mobile
    response = SMSHelper.send_to_terminal(mobile, content)
    #NOTE: send general sms to mobile
    #response = SMSHelper.send(mobile, content)
    logging.info("Response: %s", response)

def send_all(content):
    db = DBConnection().db

    terminals = db.query("SELECT * FROM V_TERMINAL WHERE cid in ( '15207610001' )")
    #terminals = db.query("select id, tid, mobile, offline_time, from_unixtime(offline_time) from T_TERMINAL_INFO where login = 0")
    #terminals = db.query("SELECT mobile FROM T_TERMINAL_INFO where login=0")
    #terminals = db.query("select id, tid, mobile, offline_time, from_unixtime(offline_time) from T_TERMINAL_INFO where login = 0")
    #terminals = db.query("select id, tid, mobile, offline_time, from_unixtime(offline_time) from T_TERMINAL_INFO where login = 0 and offline_time>1408197915")
    #terminals = db.query("select id, tid, mobile, offline_time, from_unixtime(offline_time) from T_TERMINAL_INFO where login = 0 and offline_time>1411452000")
    print 'len: %s', len(terminals)

    for t in terminals:
        terminal = db.get("select login, tid, mobile from T_TERMINAL_INFO where tid = %s", t.tid)
        if terminal.login == 0: # offline
            print '--', terminal
            send(content, terminal.mobile)

    #for terminal in terminals:
    #    print 'terminal', terminal
    #    send(content, terminal.mobile)
    #print 'len: %s', len(terminals)

def usage():
    print "Usage: python send_sms.py --send=[all|one] [--mobile=15942361934]"

def main():
    ConfHelper.load('../conf/global.conf')
    parse_command_line()
    if not 'send' in options:
        usage()
        exit(1)

    # domain for ydcws
    #content = ':DOMAIN www.ydcws.com:10025'
    #content = ':DOMAIN 211.139.215.236:10025'

    # domain for ichebao.net
    #content = ':DOMAIN 124.193.174.42:10025'
    #content = ':DOMAIN www.ichebao.net:10025'
    #content = ':DOMAIN 54.208.46.49:10027'
  
    # for Xi'an 
    #content = ':DOMAIN 222.91.127.162:10024'

    # for  CIQ 
    #content = ':DOMAIN 59.37.56.145:10024'

    #content = ':CQ test' # restart terminal

    #content = ':CQ' # restart terminal
    #content = ':REBOOT' # restart terminal

    #content = ':UPDATE' # update script

    #content = ':EVAL' # test script whether works well

    #content = ':JB'
    #content = ':SIM 13922256008:13751803006'
    #content = ':SIM 18823511110:14715437523'
    content = ':SIM 13600124555:14715437523'
    #content = ':DW'
    #content = 'test it'
    #content = 'SET QQ 3*c*15241589576'
    #content = u'尊敬的客户：您的定位器“14778471700”基站定位成功，地址：浙江省嘉兴市海盐县城北西路178-8号，红太阳药店附近，时间：2013-12-27，15:03:33。点击 http://www.ydcws.com/tl/nI3mUb 查看定位器位置。'
    content = u'尊敬的客户：您的定位器“粤T7A711”发生震动，请关注定位器状态，地址：广东省中山市市辖 区起湾南道71，华凯花园附近，时间：2014-01-03，07:56:12。如需取消短信提醒，请执行撤防操作。点击http://www.ydcws.com/tl/Fj2MRz 查看定位器位置。onent = 尊敬的客户，您之前参加的手机阅读精品阅读包0元打折体验优惠将于本月底到期，如需退订请发送QXJPYDB到10658080、或登录手机阅读网站/客户端进行退订操作。若不退订，下月起按正常资费（5元/月）收取。精品阅读包书单详见wap.cmread.com/iread/m/M6060282 手机阅读、给你好看，感谢您的支持。中国移动' 
    content = "test....."
    
    if options.send.lower() == 'all':
        send_all(content)
    elif options.send.lower() == 'one':
        if not 'mobile' in options:
            usage()
            exit(1)
        elif not options.mobile:
            usage()
            exit(1)
        # mobiles=[13703041084,13703041147,13703041294,13703041346]
        # import time
        # for mobile in mobiles:
        #     send(content, mobile)
        #     time.sleep(1)
        send(content, options.mobile)
    else:
        usage()
        exit(1)


if __name__ == "__main__": 
    main()
