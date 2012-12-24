# -*- coding: utf-8 -*-

import logging

from oracledb import Connection

from helpers.confhelper import ConfHelper

from utils.dotdict import DotDict

from exceptions import UninitializedConfiguration

def get_connection():
    if not ConfHelper.loaded:
        logging.error("Please run load_config(conf_file) before setting up connections.")
        raise UninitializedConfiguration("use ConfHelper before initialized.")

    return Connection(host=ConfHelper.ORACLE_CONF.host,
                      database=ConfHelper.ORACLE_CONF.database,
                      user=ConfHelper.ORACLE_CONF.user,
                      password=ConfHelper.ORACLE_CONF.password)

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


DBConnection = _SingletonDBConnection
