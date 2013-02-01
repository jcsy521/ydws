#!/usr/bin/python
# -*- coding: UTF-8 -*-

import re
import time
import paramiko 
import logging
import os.path


from tornado.escape import json_decode, json_encode
from tornado.options import define, options, parse_command_line

from fileconf import FileConf    
from db import DBConnection

TOP_DIR_ = os.path.abspath(os.path.join(__file__, "../../.."))
# NOTE: here, define the log server
_conf_file = os.path.join(TOP_DIR_, "log/file/")
_conf_recod = os.path.join(TOP_DIR_, "log/handlers/")

#define('mode', default='deploy')
#options['logging'].set('warning')

class DoFile(object):

    fc = FileConf()
    db = DBConnection().db
    filelist = fc.getFilePath()

    _error_pattern = r"Error"
    ERROR_CHECKER = re.compile(_error_pattern, re.I)

    _exception_pattern = r"(Exception|failed|Warni|Warning)"
    EXCEPTION_CHECKER = re.compile(_exception_pattern, re.I)
        
    def file_celery(self, filename, servername, startline, endnum):  
        """
        @params:  filename--> the name of error file
                  servername --> the name while the server belong to
                  startline --> the begin line
                  endnumstr --> the position of last read 
        @returns: lil --> a list, keep the startline, endunm of the file          
        workflow:
        line = r.readlin()
        if startline = line: # the same file
            f.seek(endnum)
            line = f.readline()
        else: # a new file
        while line:
            level = find the word of the line
            if level:
               inser the line to T_LOG_DETAILS 
               while True:
                  error = f.readline() 
                  flag = find time of the line 
                  if flag:
                      break
                  else:
                      insert the line to T_LOG_ERROR 
                          
        li1.append(startline)
        li1.append(endnum)
        """

        li1 = []
        f = open(filename,"r")
        line = f.readline()
        try:
            if startline == unicode(line.decode('utf-8')):
                endnum = endnum if endnum else 0
                f.seek(endnum)
                line = f.readline()
            else: #: # the file has been roldback
                startline = line
            while line:
                forward = True
                level = re.findall(r"(WARNI|ERROR\/)",line)           
                if level:
                    time = re.findall(r"([0-9]{4}-[0-9]{2}-[0-9]{2}"
                                      " [0-9]{2}:[0-9]{2}:[0-9]{2})", 
                                      line)
                    detail = re.findall(r"(,.*)",line)
                    about = self.db.execute("INSERT INTO T_LOG_DETAILS"
                                            "  (time, level, servername, details)"
                                            "  VALUES(%s, %s, %s, %s)", 
                                            time[0], level[0][:-1],
                                            servername, detail[0][1:500])
                        
                    while True:
                        line = f.readline()
                        if not line:
                            break
                        flag = re.findall(r"([0-9]{4}-[0-9]{2}-[0-9]{2}"
                                          " [0-9]{2}:[0-9]{2}:[0-9]{2})", 
                                          line)
                        if not flag:
                            self.db.execute("INSERT INTO T_LOG_ERROR(about, details)"
                                            "  VALUES(%s, %s)", 
                                            about, line[0:2500])
                        else:
                            forward = False
                            break
                            
                if forward:
                    line = f.readline() 
            logging.info("Log for celery has finished!")        
            endnum = f.tell()
            
        except:
            logging.exception("Read Celery File Failed!")
        finally:
            li1.append(startline)
            li1.append(endnum)
            f.close()
        return  li1

    def file_java(self, filename, servername, startline, endnum):  
        """ handle the error file on java, like file_celery
        """
        li1 = []
        f = open(filename,"r")
        line = f.readline()
        try:
            if startline == unicode(line.decode('utf-8')):
                endnum = endnum if endnum else 0
                f.seek(endnum)
                line = f.readline()
            else:
                startline = line
            while line:
                forward = True
                level = re.findall(r"( ERROR| WARN)",line)           
                if level:
                    time = re.findall(r"([0-9]{4}.[0-9]{2}.[0-9]{2}"
                                      " [0-9]{2}:[0-9]{2}:[0-9]{2})", 
                                      line)
                    _time = time[0][0:4]+'-'+time[0][5:7]+'-'+time[0][8:]
                    detail = re.findall(r"((\..*)|(\].*))",line)
                    about = self.db.execute("INSERT INTO T_LOG_DETAILS"
                                            "  (time, level, servername, details) "
                                            "  VALUES(%s, %s, %s, %s)", 
                                            _time, level[0][1:],
                                            servername, detail[0][0][1:500])
                    while True:
                        line = f.readline()
                        if not line:
                            break
                        flag = re.findall(r"([0-9]{4}.[0-9]{2}.[0-9]{2}"
                                          " [0-9]{2}:[0-9]{2}:[0-9]{2})", 
                                         line)
                        if not flag:
                            self.db.execute("INSERT INTO T_LOG_ERROR(about, details)"
                                            "  VALUES(%s, %s)", 
                                            about, line[0:2500])
                        else:
                            forward = False 
                            break
                if forward:        
                    line = f.readline()       
            logging.info("Log for java has finished!")
            endnum = f.tell()
            
        except Exception as e:
            logging.exception("Read Java File Failed! Exception: %s", e.args)
        finally:
            li1.append(startline)
            li1.append(endnum)
            f.close()
        return  li1

    def file_python(self, filename, servername, startline, endnum):
        """ handle the error file on python, like file_celery
        """
        li1 = []
        f = open(filename,"r")
        line = f.readline()
        try:
            if startline == unicode(line.decode('utf-8')):
                endnum = endnum if endnum else 0
                f.seek(endnum)
                line = f.readline()
            else:
                startline = line
            while line:
                forward = True
                level = re.findall(r"(\WE |\WW )",line)             
                if  level:
                    if level[0] == "[E ":

                        if self.EXCEPTION_CHECKER.search(line):           
                        #if re.findall(r"(Exception)",line):
                            timess = re.findall(r"([0-9]{6}"
                                                " [0-9]{2}:[0-9]{2}:[0-9]{2})", 
                                                line)
                            new_now = time.strptime(timess[0], "%y%m%d %H:%M:%S" )
                            str_now = time.strftime("%Y-%m-%d %H:%M:%S", new_now)
                            detail = re.findall(r"( [a-zA-Z]+:[0-9]+].*)",line)                  
                            about = self.db.execute("INSERT INTO T_LOG_DETAILS"
                                                    "  (time, level, servername, details) "
                                                    "  VALUES(%s, 'EXCEPTION', %s, %s)",
                                                    str_now, servername,
                                                    detail[0][1:500])                    
                            while True:
                                line = f.readline()
                                if not line:
                                    break
                                flag = re.findall(r"([0-9]{6}"
                                                  " [0-9]{2}:[0-9]{2}:[0-9]{2})", 
                                                  line)
                                if not flag:
                                    self.db.execute("INSERT INTO T_LOG_ERROR"
                                                    "  (about, details)" 
                                                    "  VALUES(%s, %s)", 
                                                    about, line[1:2500])
                                else:
                                    forward = False
                                    break
                        if self.ERROR_CHECKER.search(line):           
                        #elif re.findall(r"(error)",line) :
                            timess = re.findall(r"([0-9]{6}"
                                                " [0-9]{2}:[0-9]{2}:[0-9]{2})", 
                                                line)
                            new_now = time.strptime(timess[0], "%y%m%d %H:%M:%S" )
                            str_now = time.strftime("%Y-%m-%d %H:%M:%S", new_now)
                            detail = re.findall(r"( [a-zA-Z]+:[0-9]+].*)",line)                  
                            if detail and detail[0]:
                                about = self.db.execute("INSERT INTO T_LOG_DETAILS"
                                                        "  (time, level, servername, details) "
                                                        "  VALUES(%s, 'ERROR', %s, %s)",
                                                        str_now, servername,
                                                        detail[0][1:500])                    

                                while True:
                                    line  = f.readline()
                                    if not line:
                                        break
                                    flag = re.findall(r"([0-9]{6}"
                                                      " [0-9]{2}:[0-9]{2}:[0-9]{2})", 
                                                      line)
                                    if not flag:
                                        self.db.execute("INSERT INTO T_LOG_ERROR"
                                                        "  (about, details)"
                                                        "  VALUES(%s, %s)",
                                                        about, line[1:2500])          
                                    else:
                                        forward = False
                                        break
                            else:
                                pass
                    if level[0] == "[W ":
                        exception = re.findall(r"(Exception)",line) 
                        if exception:
                            timess = re.findall(r"([0-9]{6}"
                                                " [0-9]{2}:[0-9]{2}:[0-9]{2})", 
                                                line)
                            new_now = time.strptime(timess[0], "%y%m%d %H:%M:%S" )
                            str_now = time.strftime("%Y-%m-%d %H:%M:%S", new_now)
                            detail = re.findall(r"( [a-z]+:[0-9]+].*)",line)                  
                            about = self.db.execute("INSERT INTO T_LOG_DETAILS"
                                                    "  (time, level, servername, details) "
                                                    "  VALUES(%s, 'EXCEPTION', %s, %s)",
                                                    str_now, servername,
                                                    detail[0][1:500])                            
                if forward:
                    line = f.readline()
            logging.info("Log for python has finished![the new file]")
            endnum = f.tell()
        except Exception as e:
            logging.exception("Read Python File Failed! Exception: %s", e.args)
        finally:
            li1.append(startline)
            li1.append(endnum)
            f.close()
        return  li1
    
    def getLogRec(self):
        f_rec = open(_conf_recod+"record.rgl","r")
        li_dict = {}
        try:
            li_line = f_rec.readlines() 
            if re.findall(r"({.*})",li_line[0]) :
                li_dict = json_decode(li_line[0])
            else:
                li_dict = {}    
        except Exception as e:
            li_dict={}
            logging.exception("Read record.rgl failed! Exception: %s", e.args)      
        finally:
            f_rec.close()
            return li_dict
            
    def saveLogRec(self,save_dict):
        f_save = open(_conf_recod+"record.rgl","w")
        f_save.write(json_encode(save_dict))
        f_save.close()

    def dofile(self):  

        save_message = self.fc.getSaveInfo() 
        record_dict = self.getLogRec() 

        for file in self.filelist:
            try:
                conf_url = file.get("url")   
                conf_username = file.get("username") 
                conf_password = file.get("password") 
                conf_remotepath = file.get("remotepath") 
                conf_servername = file.get("servername")
                conf_logmodel = file.get("logmodel")
                conf_sessionname = file.get("sessionname")
                socks=(conf_url,22)
                testssh=paramiko.Transport(socks)
                testssh.connect(username=conf_username,password=conf_password)
                sftptest=paramiko.SFTPClient.from_transport(testssh)                   
                sftptest.get(conf_remotepath,_conf_file+"error.log")
                sftptest.close()
                testssh.close()
                logging.info(conf_sessionname+"log get success")
                if conf_logmodel == "java":
                    logging.info("come to java module!") 
                    li_save=  self.file_java(_conf_file+"error.log",
                                             conf_servername,
                                             record_dict.get(conf_sessionname+"_starline"),
                                             record_dict.get(conf_sessionname+"_endnum"))
                    record_dict[conf_sessionname] = conf_sessionname
                    record_dict[conf_sessionname+"_starline"] = li_save[0]
                    record_dict[conf_sessionname+"_endnum"] = li_save[1]
                elif conf_logmodel == "python":
                    logging.info("come to python module!") 
                    li_save =  self.file_python(_conf_file+"error.log",
                                                conf_servername,
                                                record_dict.get(conf_sessionname+"_starline"),
                                                record_dict.get(conf_sessionname+"_endnum"))
                    record_dict[conf_sessionname] = conf_sessionname
                    record_dict[conf_sessionname+"_starline"] = li_save[0]
                    record_dict[conf_sessionname+"_endnum"] = li_save[1]
                elif conf_logmodel == "celery":
                    logging.info("come to celery module!") 
                    li_save =  self.file_celery(_conf_file+"error.log",
                                                conf_servername,
                                                record_dict.get(conf_sessionname+"_starline"),
                                                record_dict.get(conf_sessionname+"_endnum"))
                    record_dict[conf_sessionname] = conf_sessionname
                    record_dict[conf_sessionname+"_starline"] = li_save[0]
                    record_dict[conf_sessionname+"_endnum"] = li_save[1]
                else:
                    logging.exception("Logmodels only can be celery, jave, python, check the monitor.conf again!") 
                # after the handler, remove the file
                os.remove(_conf_file+"error.log")
                logging.info(conf_sessionname+"deal with file success")
            except Exception as e:
                logging.exception("Handle files fail. Exception: %s", e.args)
                    
        self.saveLogRec(record_dict)            

        try:
            self.db.execute("DELETE FROM T_LOG_DETAILS "
                            "  WHERE time < DATE_SUB(now(),"
                            "  INTERVAL %s DAY)",
                            save_message)
            logging.info("Clean up the outdate data in database")
        except Exception as e:
            logging.exception("Clean up old data failed! Exception: %s", e.args)
    
if __name__=="__main__":
    parse_command_line()
    df = DoFile()
    df.dofile()
