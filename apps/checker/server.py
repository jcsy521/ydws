#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os.path
import site
import os

TOP_DIR_ = os.path.abspath(os.path.join(__file__, "../../.."))
site.addsitedir(os.path.join(TOP_DIR_, "libs"))

import time
import logging
import thread

import tornado
from tornado.options import define, options
define('conf', default=os.path.join(TOP_DIR_, "conf/global.conf"))
# deploy or debug
define('mode', default='deploy')
# use warning for deployment
options['logging'].set('info')

from utils.myredis import MyRedis
from db_.mysql import DBConnection
from helpers.confhelper import ConfHelper

from checkterminalstatus import CheckTerminalStatus
from terminal import SimulatorTerminal
from terminal_test import SimulatorTerminalTest
from checkservice import CheckService
from checkdb import CheckDB


def usage():
    print "python26 server.py --conf=/path/to/conf_file"

def check_db():
    logging.info("[CK] check db thread started...")
    cdb = CheckDB() 
    try:
        while True:
            time.sleep(10)
            cdb.update_clatclon()
    except Exception as e:
        logging.exception("[CK] Start check db failed.")

def check_terminal_status():
    logging.info("[CK] check terminal status thread started...")
    cps = CheckTerminalStatus() 
    try:
        while True:
            time.sleep(60)
            cps.check_terminal_status()
    except Exception as e:
        logging.exception("[CK] Start check terminals status failed.")

def simulator_terminal():
    logging.info("[CK] simulator terminal thread started...")
    st = SimulatorTerminal() 
    time.sleep(10)
    try:
        st.udp_client()
    except Exception as e:
        logging.exception("[CK] Start check simulator terminal failed.")

def simulator_terminal_test():
    logging.info("[CK] simulator terminal thread started...")
    st = SimulatorTerminalTest() 
    time.sleep(10)
    try:
        st.udp_client()
    except Exception as e:
        logging.exception("[CK] Start check simulator terminal failed.")

def check_service():
    logging.info("[CK] check service thread started...")
    cs = CheckService() 
    try:
        cs.check_service()
    except Exception as e:
        logging.exception("[CK] Start check service failed.")

def main():
    tornado.options.parse_command_line()
    if not ('conf' in options):
        import sys
        usage()
        sys.exit(1)

    if options.mode.lower() == "debug":
        debug_mode = True
    else:
        debug_mode = False

    ConfHelper.load(options.conf)

    try:
        logging.warn("[CK] running on: localhost. Parent process: %s", os.getpid())
        thread.start_new_thread(check_terminal_status, ())
        thread.start_new_thread(check_service, ())
        thread.start_new_thread(simulator_terminal, ())
        thread.start_new_thread(simulator_terminal_test, ())
        #thread.start_new_thread(check_db, ())
        while True:
            time.sleep(60)
         
    except KeyboardInterrupt:
        logging.error("Ctrl-C is pressed.")
    except:
        logging.exception("[checker] Exit Exception")
    finally:
        logging.warn("[CK] shutdown...")
        logging.warn("[CK] stopped. Bye!")


if __name__ == '__main__':
    main()
