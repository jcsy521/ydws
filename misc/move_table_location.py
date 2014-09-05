# -*- coding: utf-8 -*-

import sys
import os.path
import site
import time
TOP_DIR_ = os.path.abspath(os.path.join(__file__, "../.."))
site.addsitedir(os.path.join(TOP_DIR_, "libs"))
import logging

from tornado.options import define, options, parse_command_line
from helpers.confhelper import ConfHelper
from helpers.smshelper import SMSHelper
from db_.mysql import DBConnection


def move_data():
    db = DBConnection().db
       
    mobiles = ['18310505991', '13693675352', '13581731204']
    message = "数据库T_LOCATION已经完全转移到T_LOCATION_NEW,请及确认表信息的正确性和完整性。"
    #max_row = 1000000000
    max_row = 250000000
    begin_time = time.gmtime(time.time())
    for i in range(10000, max_row, 10000):
        sql = "INSERT INTO T_LOCATION_NEW" \
              " SELECT * FROM T_LOCATION WHERE id <=%d AND id > %d -10000" \
              " and (timestamp between 0 and 1448899200)" % (i, i)
        logging.info("exectue sql:%s", sql)
        
        n = db.execute(sql)
        #time.sleep(0.1)
        logging.info("last record  row id =%s", n)
        break
       # if i = 250000000:
        if i == 240000000:
            for mobile in mobiles:
                SMSHelper.send(mobile, message)    
                print "send", mobile
    end_time = time.gmtime(time.time())
    L_bak = "alter table T_LOCATION rename  to T_LOCATION_bak"
    NEW_L = "alter table T_LOCATION_NEW rename  to T_LOCATION"
    
    for i in range(1, 5): 
        time.sleep(1)
        logging.info("Will rename table neame after %d second", 5-i)
    
    db.execute(L_bak)
    db.execute(NEW_L)
    logging.info("exchange tables T_LOCATION and T_LOCATION_NEW is accomplished ")
    logging.info("Move table data begin_time:%s, end_time:%s", begin_time, end_time)

def usage():
    print "Usage: python move_data.py "

def main():
    ConfHelper.load('../conf/global.conf')
    parse_command_line()
    
    move_data()

if __name__ == "__main__":
    main()

