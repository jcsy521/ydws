# -*- coding: utf-8 -*-

import socket, select, errno 

import os
import logging
import time
import pika
from pika.adapters import *
from pika.exceptions import AMQPConnectionError, AMQPChannelError
import json
from Queue import Queue, Empty
import thread
import multiprocessing

from utils.dotdict import DotDict
from db_.mysql import DBConnection
from utils.myredis import MyRedis

from helpers.confhelper import ConfHelper
  
from handlers.base import Base 
from mixin.mq import RabbitMQMixin 

from error import GWException

class MyGWServer(RabbitMQMixin):
    """
    GWServer communicate with terminals.
    It receive MT packets from terminals and handle them, And send MO
    packets to terminals.

    There are two process: 
      - publish process(recv packets and put response into queue)
      - consume process(send packets from queue)
    """

    def __init__(self, conf_file):
        ConfHelper.load(conf_file)

        for i in ('port', 'count', 'check_heartbeat_interval'):
            ConfHelper.GW_SERVER_CONF[i] = int(ConfHelper.GW_SERVER_CONF[i])

        #NOTE: define some variable 
        self.check_heartbeat_thread = None
        self.db_list = []
        self.exchange = 'ydws_exchange'
        self.gw_queue = 'ydws_gw_requests_queue@' +\
                        ConfHelper.GW_SERVER_CONF.host + ':' +\
                        str(ConfHelper.GW_SERVER_CONF.port)
        self.si_queue = 'ydws_si_requests_queue@' +\
                        ConfHelper.SI_SERVER_CONF.host + ':' +\
                        str(ConfHelper.SI_SERVER_CONF.port)
        self.gw_binding = 'ydws_gw_requests_binding@' +\
                          ConfHelper.GW_SERVER_CONF.host + ':' +\
                          str(ConfHelper.GW_SERVER_CONF.port)
        self.si_binding = 'ydws_si_requests_binding@' +\
                          ConfHelper.SI_SERVER_CONF.host + ':' +\
                          str(ConfHelper.SI_SERVER_CONF.port)

        #NOTE: initialize socket 
        self.socket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((ConfHelper.GW_SERVER_CONF.host, ConfHelper.GW_SERVER_CONF.port))

    def consume(self, host):
        """Consume connection.

        workflow:
        1. get packet from rabbitmq_queue
        2. send packet to terminal
        """
        logging.info("[GW] Consume process, name: %s, pid: %s started...", 
                     multiprocessing.current_process().name, os.getpid())
        try:
            print 1
            consume_connection, consume_channel = self.connect_rabbitmq(host)
            while True:
                try:
                    method, header, body = consume_channel.basic_get(queue=self.gw_queue)
                    if method.NAME == 'Basic.GetEmpty':
                        time.sleep(0.1) 
                    else:
                        consume_channel.basic_ack(delivery_tag=method.delivery_tag)
                        self.send(body)
                except AMQPConnectionError as e:
                    logging.exception("[GW] Rabbitmq consume error: %s", e.args)
                    consume_connection, consume_channel = self.reconnect_rabbitmq(consume_connection, host)
                    continue 
        except KeyboardInterrupt:
            logging.warn("[GW] Ctrl-C is pressed")
        except GWException:
            logging.exception("[GW] GW Exception...")
        except Exception:
            logging.exception("[GW] Unknow Exception...")
        finally:
            logging.info("[GW] Rabbitmq consume connection close...")
            self.close_rabbitmq(consume_connection, consume_channel)

    def send(self, body):
        """Send packet to terminal.
        """
        try:
            message = json.loads(body)
            message = DotDict(message)
            logging.info("[GW] Send packet: %s to dev_id: %s, address: %s", message.packet, message.dev_id, message.address)
            self.socket.sendto(message.packet, tuple(message.address))
        except socket.error as e:
            logging.exception("[GW] Sock send error: %s", e.args)
        except Exception as e:
            logging.exception("[GW] Unknown send Exception:%s", e.args)

    def publish(self, host):
        """Publish connection. 
        Multithread.

        1. get packet from terminal
        2. put this packet into queue
        3. handle packets of queue by multi threads
        """

        logging.info("[GW] Publish process, name: %s, pid: %s started...", 
                     multiprocessing.current_process().name, os.getpid())
        try:
            queue = Queue()
            #NOTE: multi threads handle packets
            publish_connection, publish_channel = self.connect_rabbitmq(host)
            for i in range(int(ConfHelper.GW_SERVER_CONF.workers)):
                db = DBConnection().db
                #NOTE: just record the db in list, for the close when exit.
                self.db_list.append(db)
                logging.info("[GW] publish thread%s started...", i)
                thread.start_new_thread(self.handle_packets_from_terminal,
                                        (queue, host, publish_connection, publish_channel, i, db))
            #NOTE: recv packet and put it into queue
            while True:
                self.recv(queue)
        except KeyboardInterrupt:
            logging.warn("[GW] Ctrl-C is pressed")
        except GWException as e:
            logging.exception("[GW] Unknow Exception: %s", e.args)
        finally:
            logging.info("[GW] Rabbitmq publish connection close...")
            self.close_rabbitmq(publish_connection, publish_channel)

    def recv(self, queue):
        """Recv packet from terminal.
        """
        try:
            response, address = self.socket.recvfrom(1024)
            logging.info("[GW] Recv: %s from %s", response, address)
            if response:
                item = dict(response=response,
                            address=address)
                queue.put(item)
        except socket.error as e:
            logging.exception("[GW] Sock recv error: %s", e.args)
            # reconnect socket?
            self.__close_socket()
            time.sleep(0.1)
            self.socket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((ConfHelper.GW_SERVER_CONF.host, ConfHelper.GW_SERVER_CONF.port))
        except Exception as e:
            logging.exception("[GW] Unknow recv Exception:%s", e.args)

    def handle_packets_from_terminal(self, queue, host, connection, channel, name, db):
        """Handle packets recv from terminal:

        """
        while True:
            try:
                if not connection.is_open:
                    connection, channel = self.reconnect_rabbitmq(connection, host)
                    continue
                else:
                    try:
                        if queue.qsize() != 0:
                            item  = queue.get(False)
                            packets = item.get('response')
                            address = item.get('address')
                            base = Base(db, self.redis, self.exchange, self.gw_binding, self.si_binding)
                            base.handle_packets_from_terminal(packets, address, connection, channel, name)
                        else:
                            time.sleep(0.1)
                    except Empty:
                        logging.info("[GW] Thread%s queue empty.", name)
                        time.sleep(0.1)
                    except GWException:
                        logging.exception("[GW] Thread%s handle packet Exception.", name) 
            except:
                logging.exception("[GW] Thread%s recv Exception.", name)

    def __close_socket(self):
        """Close socket.
        """
        try:
            self.socket.close()
        except Exception as e:
            logging.exception("[GW] Close socket Failed. Exception: %s.",
                              e.args)

    def stop(self):
        """Stop socket, memcached, db
        """
        self.__close_socket()
        for db in self.db_list:
            db.close()

    def __del__(self):
        """Invoke stop method.
        """
        self.stop()
