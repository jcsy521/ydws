# -*- coding: utf-8 -*-

import ConfigParser
from utils.dotdict import DotDict


class ConfHelper(object):
    """Load sender (and/or sms) configurations from conf file and
    provide them as global variables.
    """
    # prevent for multiple loads
    _HAVE_LOADED = False

    @property
    @classmethod
    def loaded(cls):
        return cls._HAVE_LOADED
    
    @classmethod
    def load(cls, conf_file):
        """load definitoins from conf_file."""
        print 1
        if cls._HAVE_LOADED:
            return
        
        print '2', conf_file
        cfg = ConfigParser.ConfigParser()
        cfg.read(conf_file)

        for section in cfg.sections():
            sec_conf = section.upper() + "_CONF"
            print '3', sec_conf 
            setattr(cls, sec_conf, DotDict())
            for k, v in cfg.items(section):
                getattr(cls, sec_conf)[k.lower()] = v

        print '--', cls.REDIS_CONF
        cls._HAVE_LOADED = True
