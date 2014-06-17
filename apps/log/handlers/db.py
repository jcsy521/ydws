# -*- coding: utf-8 -*-

import logging

try:
    from tornado.database import Connection
except:
    from torndb import Connection

from fileconf import FileConf

def get_connection():
    
    fileconf = FileConf()
    db_info = fileconf.getDB()
    db_host = db_info.get("db_host")
    #print 'host=', db_host
    db_name = db_info.get("db_name")
    db_user = db_info.get("db_user")
    db_pass = db_info.get("db_pass")   
    return Connection(db_host,db_name,db_user,db_pass)    

class _SingletonDBConnection(object):

    class __impl:
        
        def __init__(self):
            self.db = get_connection()

    __instance = None

    def __init__(self):
        if self.__instance is None:
            self.__instance = self.__impl()
        
    @property
    def db(self):
        return self.__instance.db


DBConnection = _SingletonDBConnection
