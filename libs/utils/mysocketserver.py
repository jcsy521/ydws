# -*- coding: utf-8 -*-


import socket
import logging
import time

import json
from utils.dotdict import DotDict
from helpers.confhelper import ConfHelper


class MySocketServer(object):

    """ """

    def __init__(self, address):
        """ """
        assert ConfHelper.loaded
        self.address = address

        self.create_socket(address)

    def create_socket(self, address):
        """Create a TCP/IP socket server.
        """
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # avoid the error: `socket.error: [Errno 98] Address already in use`
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # bind it as socket server.
        self.socket.bind(address)

    def send(self, body):
        """Send packet to terminal.
        """
        try:            
            message = json.loads(body)          
            message = DotDict(message)
            logging.info("[GW] Send packet: %s to dev_id: %s, address: %s", 
                         message.packet, message.dev_id, message.address)
            self.socket.sendto(message.packet, tuple(message.address))
        except socket.error as e:
            logging.exception("[GW] Sock send error: %s", e.args)
        except Exception as e:
            logging.exception("[GW] Unknown send Exception:%s", e.args)

    def recv(self):
        """Receive packets from terminal and keep it in the packet_queue.

        workflow:
            packet = recv_from_terminal
            packet_queue.put(packet)
        """
        response = None
        address = ()
        try:
            response, address = self.socket.recvfrom(1024)
            # logging.info("[GW] Recv: %s from %s", response, address)
            # if response:
            #     item = dict(response=response,
            #                 address=address)
            #     self.packet_queue.put(item)
        except socket.error as e:
            logging.exception("[GW] Sock recv error: %s", e.args)
            # reconnect socket
            self.close_socket()
            time.sleep(0.1) 
            self.create_socket(self.address)           
        except Exception as e:
            logging.exception("[GW] Unknow recv Exception:%s", e.args)

        return response, address

    def close_socket(self):
        """Close socket.
        """
        try:
            if hasattr(self, 'socket'):
                self.socket.close()
        except Exception as e:
            logging.exception("[GW] Close socket Failed. Exception: %s.",
                              e.args)
