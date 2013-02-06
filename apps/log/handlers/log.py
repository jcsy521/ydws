# -*- coding: UTF-8 -*-

import tornado.web
from tornado.escape import  json_decode  

from utils.dotdict import DotDict
from base import authenticated,BaseHandler
 

class Log(BaseHandler):
    
    @authenticated
    def get(self):

        username = self.get_current_user()
        self.render("log.html",
                     allLog={},
                     pagecnt=-1,
                     pagenum=0,
                     beginDate="",
                     endDate="",
                     plan_id="",
                     level="",
                     username=username,)
        return

    @authenticated
    @tornado.web.removeslash
    def post(self):
        log = json_decode(self.request.body)                     
        beginDate = log.get("beginDate")
        endDate = log.get("endDate")
        plan_id = log.get("plan_id")
        pagecnt = log.get("pagecnt")
        pagenum = log.get("pagenum")
        level = log.get("level")
        if level:
            if  beginDate:
                try: 
                    if plan_id:
                        if pagecnt == -1:
                            allNum = self.db.get("SELECT COUNT(*) AS num FROM T_LOG_DETAILS"
                                                 "  WHERE servername = %s"
                                                 "  AND time BETWEEN %s AND %s"
                                                 "  AND level = %s", 
                                                 plan_id, beginDate, endDate, level)
                            pagecnt = (allNum.num-1)/20+1
                            #pagecnt = (int(allNum.get("count(*)"))-1)/20+1
                        allLog = self.db.query("SELECT id, level, servername, details,"
                                               "  DATE_FORMAT(time, '%%Y-%%m-%%d %%H:%%i:%%s')"
                                               "  AS  time FROM T_LOG_DETAILS"
                                               "    WHERE servername = %s"
                                               "      AND time BETWEEN %s AND %s" 
                                               "      AND level = %s"
                                               "    ORDER BY time DESC LIMIT %s, 20", 
                                               plan_id, beginDate, endDate, level, pagenum*20)
                        self.write_ret(0, message=None, 
                                       dict_=DotDict(loglist=allLog, pagecnt=pagecnt))
                    else:
                        if pagecnt == -1:
                            allNum = self.db.get("SELECT COUNT(*) AS num FROM T_LOG_DETAILS"
                                                 "  WHERE time BETWEEN %s AND %s"
                                                 "  AND level = %s", 
                                                 beginDate, endDate, level)

                            pagecnt = (allNum.num-1)/20+1
                            #pagecnt = (int(allNum.get("count(*)"))-1)/20+1
                        allLog = self.db.query("SELECT id, level, servername, details,"
                                               "  DATE_FORMAT(time,'%%Y-%%m-%%d %%H:%%i:%%s')"
                                               "  AS time FROM T_LOG_DETAILS"
                                               "    WHERE time BETWEEN %s AND %s" 
                                               "    AND level = %s"
                                               "    ORDER BY time DESC LIMIT %s, 20", 
                                               beginDate, endDate, level, pagenum*20)
                        self.write_ret(0, message=None, 
                                       dict_=DotDict(loglist=allLog, pagecnt=pagecnt))
                except:
                    self.write_ret(500, message=u"查询错误", dict_=None)
            else:#if time is null
                self.render("log.html",
                            allLog={},
                            pagecnt=-1,
                            nowpage=1,
                            beginDate="",
                            endDate="",
                            plan_id="",
                            level="",
                            username=None,)
                return
        else:   
            if  beginDate:#have time's value
                try: 
                    if plan_id:#have the plan_id value  try:    except
                        if pagecnt==-1:
                            allNum = self.db.get("SELECT COUNT(*) AS num FROM T_LOG_DETAILS "
                                                 "  WHERE servername = %s" 
                                                 "  AND time BETWEEN %s AND %s", 
                                                 plan_id, beginDate, endDate)
                            pagecnt = (allNum.num-1)/20+1
                            #pagecnt = (int(allNum.get("count(*)"))-1)/20+1
                        allLog = self.db.query("SELECT id, level, servername, details,"
                                               "  DATE_FORMAT(time,'%%Y-%%m-%%d %%H:%%i:%%s')"
                                               "  AS time FROM T_LOG_DETAILS" 
                                               "    where servername=%s"
                                               "    AND time BETWEEN %s AND %s" 
                                               "    ORDER BY time DESC LIMIT %s, 20 ", 
                                               plan_id, beginDate, endDate, pagenum*20)
                        self.write_ret(0, message=None,
                                       dict_=DotDict(loglist=allLog, pagecnt=pagecnt))
                    else:
                        if pagecnt==-1:
                            allNum = self.db.get("SELECT COUNT(*) AS num FROM T_LOG_DETAILS "
                                                 "  WHERE time BETWEEN %s AND %s", 
                                                 beginDate, endDate)
                            #pagecnt = (int(allNum.get("count(*)"))-1)/20+1
                            pagecnt = (allNum.num-1)/20+1
                        allLog = self.db.query("SELECT id, level, servername, details,"
                                               "  DATE_FORMAT(time,'%%Y-%%m-%%d %%H:%%i:%%s')"
                                               "  AS time FROM T_LOG_DETAILS "
                                               "    WHERE time BETWEEN %s AND %s "
                                               "    ORDER BY time DESC LIMIT %s, 20", 
                                               beginDate, endDate, pagenum*20)
                        self.write_ret(0, message=None, 
                                       dict_=DotDict(loglist=allLog, pagecnt=pagecnt))
                except:
                    self.write_ret(500, message=u"查询错误", dict_=None)
            else:
                self.render("log.html",
                            allLog={},
                            pagecnt=-1,
                            nowpage=1,
                            beginDate="",
                            endDate="",
                            plan_id="",
                            level="",
                            username=None,)
                return
