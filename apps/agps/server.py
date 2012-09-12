#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os.path
import site
import socket, select
import logging
import base64
import time

TOP_DIR_ = os.path.abspath(os.path.join(__file__, "../../.."))
site.addsitedir(os.path.join(TOP_DIR_, "libs"))

from utils import options
options.define('conf', default=os.path.join(TOP_DIR_, "conf/global.conf"))
options.options['logging'].set('info')

from utils.misc import get_agps_data_key, get_terminal_sessionID_key
from utils.repeatedtimer import RepeatedTimer
from utils.dotdict import DotDict

from utils.myredis import MyRedis
from helpers.confhelper import ConfHelper
from constants import GATEWAY

from agps.packet.parser.codecheck import T_CLWCheck
from agps.packet.parser.agpsparser import AgpsParser 
from agps.packet.composer.agpscomposer import AgpsComposer


class AgpsServer(object):

    def __init__(self, conf_file):
        ConfHelper.load(conf_file)
        self.redis = MyRedis() 
        self._socket = None
        self.get_agps_thread = None
        
    def start(self):
        self.__start_get_agps_thread()
        try: 
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.bind((ConfHelper.AGPS_CONF['host'], int(ConfHelper.AGPS_CONF['port'])))
            self._socket.listen(int(ConfHelper.AGPS_CONF['count']))
            while True:
                try:
                    infds, _, _ = select.select([self._socket,],[],[],1)
                    if len(infds) > 0:
                        connection, address = self._socket.accept()
                        data = connection.recv(1024)
                        logging.info("[AGPS] Recv request:\n%s", data)
                        agps_data = self.handle_request(data)
                        if agps_data:
                            connection.send(agps_data)
                            logging.info("[AGPS] Send response:\n%s", agps_data)
                            connection.close()
                except KeyboardInterrupt:
                    logging.error("[AGPS] Ctrl-C is pressed.") 
                    self._socket.close()
        except:
            logging.exception("[AGPS] Socket exception.") 
        finally:
            try:
                self._socket.close()
            except:
                logging.exception("[AGPS] Socket close exception")

    def handle_request(self, data):
        try:
            packet = T_CLWCheck(data)
            command = packet.head.command
            if command == GATEWAY.T_MESSAGE_TYPE.AGPS:
                head = packet.head
                body = packet.body 
                args = DotDict(success=GATEWAY.RESPONSE_STATUS.SUCCESS,
                               agps_data="")
                ap = AgpsParser(body, head)
                agps_sign = self.get_agps_sign(ap.ret, int(head.timestamp))
                if agps_sign != int(head.agps_sign, 16):
                    args.success = GATEWAY.RESPONSE_STATUS.INVALID_SESSIONID
                else:
                    agps = ap.ret
                    args.agps_data = self.get_agps_from_redis(agps)
                    ac = AgpsComposer(args)
                    return ac.buf
        except:
            logging.exception("[AGPS] Handle agps request exception.")
            return ""

    def get_agps_sign(self, agps, timestamp):
        DEFAULT_KEY = 181084178
        lon = int(float(agps.lon) * 3600000)
        lat = int(float(agps.lat) * 3600000)
        agps_sign = DEFAULT_KEY ^ lon ^ lat ^ timestamp 
        return agps_sign 
                    
    def get_agps_from_ublox(self):
        LON_LAT = GATEWAY.LON_LAT
        for key, lon_lat in LON_LAT.items():
            u_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                request = "cmd=aid;user=%s;pwd=%s;lat=%s;lon=%s;pacc=%s\n" % (
                                                    ConfHelper.UBLOX_CONF.user,
                                                    ConfHelper.UBLOX_CONF.pwd,
                                                    lon_lat[1],
                                                    lon_lat[0],
                                                    ConfHelper.UBLOX_CONF.pacc)
                u_socket.connect((ConfHelper.UBLOX_CONF.host, int(ConfHelper.UBLOX_CONF.port)))
                u_socket.send(request)
                agps_data = u_socket.recv(2048)
                agps_key = get_agps_data_key(key)
                list_agps_data = agps_data.split('application/ubx\r\n\r\n')
                if len(list_agps_data) > 1:
                    binary_data = list_agps_data[1]
                    self.redis.set(agps_key, base64.b64encode(binary_data))
                    logging.info("[AGPS] Get agps data [%s] from ublox success.", key)
                else:
                    # delete or not
                    # self.redis.delete(agps_key)
                    logging.info("[AGPS] Get agps data [%s] from ublox faild.", key) 
            except:
                logging.exception("[AGPS] Get agps from u-blox exception.")
            finally:
                try:
                    u_socket.close()
                except:
                    logging.exception("[AGPS] U-blox socket close exception.")               
            time.sleep(10)

    def get_agps_from_redis(self, agps):
        try:
            logging.info("[AGPS] Terminal lon=%s, lat=%s", agps.lon, agps.lat)
            partition_key = self.get_partition_key(float(agps.lon), float(agps.lat))
            agps_key = get_agps_data_key(partition_key)
            agps_data = self.redis.get(agps_key)
            agps_data = agps_data if agps_data else ""
            return agps_data
        except:
            logging.exception("[AGPS] Get agps from redis exception.")
            return ""
 
    def get_partition_key(self, lon, lat):
        LON_LAT = GATEWAY.LON_LAT 
        partition_key = "default"
        for key, lon_lat in LON_LAT.items():
            if abs(float(lon_lat[0]) - lon) <= 10 and \
               abs(float(lon_lat[1]) - lat) <= 12.5:   
               partition_key = key
               break
        logging.info("[AGPS] agps partition is:%s", partition_key)
        return partition_key

    def __start_get_agps_thread(self):
        self.get_agps_thread = RepeatedTimer(int(ConfHelper.UBLOX_CONF.interval),
                                             self.get_agps_from_ublox)
        self.get_agps_thread.start()
        logging.info("[AGPS] Get agps thread is running...")

    def __stop_get_agps_thread(self):
        if self.get_agps_thread is not None:
            self.get_agps_thread.cancel()
            self.get_agps_thread.join()
            logging.info("[AGPS] Get agps thread stop.")
            self.get_agps_thread = None

    def stop(self):
        self.__stop_get_agps_thread() 
        self._socket.close()

def main():
    options.parse_command_line()
    aps = AgpsServer(options.options.conf)
    try:
        logging.info("[AGPS] running on localhost.")
        aps.start()
    except KeyboardInterrupt:
        logging.error("[AGPS] Ctrl-C is pressed.")
    except:
        logging.exception("[AGPS] Exit Exception")
    finally:
        logging.warn("[AGPS] shutdown...")
        aps.stop() 
        logging.warn("[AGPS] stopped. Bye!")


if __name__ == '__main__':
    main()
