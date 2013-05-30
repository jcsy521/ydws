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

from checkpofftimeout import Checkpofftimeout
from checkterminalstatus import CheckTerminalStatus
from chargeremind import ChargeRemind
from terminal import SimulatorTerminal
from checkservice import CheckService
from statistic import TerminalStatistic


def usage():
    print "python26 server.py --conf=/path/to/conf_file"

def check_poweroff_timeout():
    logging.info("[CK] check poweroff timeout thread started...")
    cpt = Checkpofftimeout() 
    try:
        while True:
            time.sleep(60)
            cpt.check_poweroff_timeout()
    except Exception as e:
        logging.exception("[CK] Start check terminals poweroff timeout failed.")

def check_terminal_status():
    logging.info("[CK] check terminal status thread started...")
    cps = CheckTerminalStatus() 
    try:
        while True:
            time.sleep(60)
            cps.check_terminal_status()
    except Exception as e:
        logging.exception("[CK] Start check terminals status failed.")

def charge_remind():
    logging.info("[CK] charge remind thread started...")
    ccr = ChargeRemind() 
    try:
        while True:
            time.sleep(86400)
            ccr.check_charge_remind()
    except Exception as e:
        logging.exception("[CK] Start check charge remind failed.")

def simulator_terminal():
    logging.info("[CK] simulator terminal thread started...")
    st = SimulatorTerminal() 
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

#def run_statistic_thread():
#    logging.info("[CK] statistic thread started...")
#    INTERVAL = 0
#    ONE_DAY = 60 * 60 * 24
#    ONE_HOUR = 60 * 60
#    ts = TerminalStatistic() 
#    try:
#        while True:
#            epoch_time = time.time()
#            current_time = time.strftime("%Y%m%d%H%M%S", time.localtime(epoch_time))
#            hour = current_time[8:10]
#            if hour == '12':
#                ts.statistic_online_terminal(epoch_time)
#                INTERVAL = ONE_DAY
#            else:
#                INTERVAL = ONE_HOUR
#            time.sleep(INTERVAL)
#            
#    except Exception as e:
#        logging.exception("[CK] Start statistic thread failed.")

def statistic_thread():
    logging.info("[CK] statistic thread started...")
    INTERVAL = 0
    ONE_DAY = 60 * 60 * 24
    ONE_HOUR = 60 * 60
    QUARTER_HOUR = 60 * 15 
    ts = TerminalStatistic() 
    try:
        while True:
            epoch_time = time.time()
            current_time = time.strftime("%Y%m%d%H%M%S", time.localtime(epoch_time))
            hour = current_time[8:10]
            #if hour == '11':
            #    ts.statistic_terminal(epoch_time)
            #    INTERVAL = ONE_HOUR
            #else:
            #    INTERVAL = QUARTER_HOUR

            ts.statistic_terminal(epoch_time)
            INTERVAL = ONE_HOUR
            time.sleep(INTERVAL)
            
    except Exception as e:
        logging.exception("[CK] Start statistic thread failed.")



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
        thread.start_new_thread(check_poweroff_timeout, ())
        thread.start_new_thread(check_terminal_status, ())
        thread.start_new_thread(check_service, ())
        thread.start_new_thread(charge_remind, ())
        thread.start_new_thread(simulator_terminal, ())
        #thread.start_new_thread(run_statistic_thread, ())
        thread.start_new_thread(statistic_thread, ())
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
