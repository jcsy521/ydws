# -*- coding: utf-8 -*-

import sys
import xlwt

import os.path
import site
TOP_DIR_ = os.path.abspath(os.path.join(__file__, "../.."))
site.addsitedir(os.path.join(TOP_DIR_, "libs"))
import logging

from tornado.options import define, options, parse_command_line

from helpers.confhelper import ConfHelper
from helpers.smshelper import SMSHelper
from db_.mysql import DBConnection
from utils.myredis import MyRedis
from utils.misc import get_terminal_info_key, get_lastinfo_key, get_location_key, get_track_key

def main():
    ConfHelper.load('../conf/global.conf')
    parse_command_line()
    db = DBConnection().db
    #wb = xlwt.Workbook()
    #ws = wb.add_sheet('location')
    #locations = db.query("select * from T_LOCATION where name = '广东省珠海市斗门区江珠高速公路' and type =1")
    locations = db.query("select * from T_LOCATION where tid = '330A000399'")
    print locations
    #keys = ["id","tid","latitude","longitude","altitude","clatitude","clongitude","timestamp","name","category","type","speed","degree","cellid"]
    #for i, head in enumerate(keys):
    #    ws.write(0, i, head)

    #print 'i======', i

    #for k, location in enumerate(locations):
    #    for j, key in enumerate(keys):
    #        print 'k==', k
    #        print 'j==', j
    #        print 'key==', key
    #        ws.write(k+1, j, unicode(location[key])) 
    #wb.save('doumen.xls')
        
def main2():
    import xlrd
    wb = xlwt.Workbook()
    ws = wb.add_sheet('location')

    f = open('t.log')
    j = 0 
    for line in f:
        d = line.split('|')
        for i, item in enumerate(d):
            ws.write(j, i, unicode(item))  
        j += 1

    wb.save('doumen2.xls')

def main3():
    import xlrd
    data = xlrd.open_workbook('doumen.xls')
    table = data.sheets()[0]
    nrows = table.nrows
    ncols = table.ncols
    l = []
    keys = ["id","tid","latitude","longitude","altitude","clatitude","clongitude","timestamp","name","category","type","speed","degree","cellid"]
    for i in range(nrows):
        item = dict()
        rv = table.row_values(i)
        for j, key in enumerate(keys):
            item[key] = rv[j].replace(" ", "")
        l.append(item)

    print l

if __name__ == "__main__":
    main()

