# -*- coding: utf-8 -*-

import re
import os.path

import ConfigParser 

TOP_DIR_ = os.path.abspath(os.path.join(__file__, "../../../.."))
_conf_file = os.path.join(TOP_DIR_, "conf/")


class FileConf(object):
    
    def __init__(self):
        cf = ConfigParser.ConfigParser()
        cf.read(_conf_file+"monitor.conf")
        db_host = cf.get("db", "db_host")
        db_name = cf.get("db", "db_name")
        db_user = cf.get("db", "db_user")
        db_pass = cf.get("db", "db_pass")
        self.dbdict={"db_host":db_host ,
                     "db_name":db_name,
                     "db_user":db_user,
                     "db_pass":db_pass}
        self.save_info = cf.get("message", "save_days")
        self.ls = []
        allsession = cf.sections()
        for file in allsession:
            type(file)
            if re.findall("(file)",file):
                conf_url = cf.get(file, "url")   
                conf_username = cf.get(file, "username") 
                conf_password = cf.get(file, "password") 
                conf_remotepath = cf.get(file, "remotepath") 
                conf_servername = cf.get(file, "servername")
                conf_logmodel = cf.get(file, "logmodel")
                filedict={"url":conf_url ,
                          "username":conf_username,
                          "password":conf_password,
                          "remotepath":conf_remotepath,
                          "logmodel":conf_logmodel,
                          "servername":conf_servername,
                          "sessionname":file}
                self.ls.append(filedict)
        self.log_file_path = os.path.dirname(cf.get("fileGATEWAY", "remotepath"))

    def getDB(self):
        """ get conf of mysql"""
        return self.dbdict

    def getFilePath(self):       
        """ get conf of error file in servers"""
        return self.ls

    def getSaveInfo(self):
        """ get days the data will be keep for"""
        return self.save_info

    def getLogFile(self):
        return self.log_file_path