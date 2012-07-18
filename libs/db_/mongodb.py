# -*- coding: utf-8 -*-

import logging

from pymongo import Connection

from helpers.confhelper import ConfHelper

from exceptions import UninitializedConfiguration, MongoDBException


def get_connection():
    if not ConfHelper.loaded:
        logging.error("Please run load_config(conf_file) before setting up connections.")
        raise UninitializedConfiguration("use ConfHelper before initialized.")

    try:
        host1 = ConfHelper.MONGODB_CONF.host1
        host2 = ConfHelper.MONGODB_CONF.host2
        host3 = ConfHelper.MONGODB_CONF.host3
        MONGODB_HOST = ','.join([host1,host2,host3])
        conn = Connection(MONGODB_HOST)
        mongodb = conn[ConfHelper.MONGODB_CONF.database]
        mongodb.authenticate(ConfHelper.MONGODB_CONF.user,
                             ConfHelper.MONGODB_CONF.password)

        return mongodb 
    except:
        raise MongoDBException("[MongoDB] is failed.")

class _SingletonDBConnection(object):
    """DB Singleton.
    
    Since it's not recommended to share db connection by threads, this sigleton
    should be used by the tornado application, which is a single thread inifinit loop.
    """

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


MongoDBConnection = _SingletonDBConnection
