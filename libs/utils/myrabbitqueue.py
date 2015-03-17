# -*- coding: utf-8 -*-

import logging
import pika
from pika.adapters import *
from pika.exceptions import AMQPConnectionError
from functools import partial

from helpers.confhelper import ConfHelper


class MyRabbitMQ(object):

    """Simple Queue with RabbitMQ Backend"""

    def __init__(self, exchange, queue):
        """ 
        """
        self.host = ConfHelper.RABBITMQ_CONF.host       
        self.exchange = exchange
        self.queue = queue
        self.connection, self.channel = self.__connect_rabbitmq() 

    def __connect_rabbitmq(self):
        connection = None
        channel = None
        try:
            parameters = pika.ConnectionParameters(host=self.host)
            connection = BlockingConnection(parameters)
            # # Write buffer exceeded warning threshold
            # reconnect_rabbitmq = partial(self.__reconnect_rabbitmq, (host,))
            # connection.add_backpressure_callback(reconnect_rabbitmq)
            channel = connection.channel()
            channel.exchange_declare(exchange=self.exchange,
                                     durable=False,
                                     auto_delete=True)
            channel.queue_declare(queue=self.queue,
                                  durable=False,
                                  exclusive=False,
                                  auto_delete=True)
            channel.queue_bind(exchange=self.exchange,
                               queue=self.queue,
                               routing_key=self.queue)

        except:
            logging.exception("[SI] Connect Rabbitmq-server Error!")

        return connection, channel

    def __reconnect_rabbitmq(self):
        """
        This is for catching any unpredictable AMQPConnectionError.
        Release resource for reconnect. 
        """
        logging.debug("[SI] Reconnect rabbitmq...") 
        if self.connection and self.connection.is_open:
            self.connection.close()

        try:
            self.connection, self.channel = self.__connect_rabbitmq()
            logging.info("[SI] Rabbitmq reconnected!")
        except:
            logging.exception("[SI] Connect rabbitmq error.")


    def get_queue_name(self):
        """
        """
        return self.name

    # def qsize(self):
    #     """Return the approximate size of the queue."""
    #     return self.__db.llen(self.key)

    # def empty(self):
    #     """Return True if the queue is empty, False otherwise."""
    #     return self.qsize() == 0

    # def clear_queue(self):
    #     while not self.empty():
    #         self.get_nowait()

    # def put(self, item):
    #     """Put item into the queue."""
    #     self.__db.rpush(self.key, item)

    # def get(self, block=True, timeout=None):
    #     """Remove and return an item from the queue. 

    #     If optional args block is true and timeout is None (the default), block
    #     if necessary until an item is available."""
    #     if block:
    #         item = self.__db.blpop(self.key, timeout=timeout)
    #     else:
    #         item = self.__db.lpop(self.key)
    #     return item

    # def get_nowait(self):
    #     """Equivalent to get(False)."""
    #     return self.get(False)
