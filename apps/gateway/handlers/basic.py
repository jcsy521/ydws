# -*- coding: utf-8 -*-

import pika
import json

from utils.misc import (get_terminal_address_key, get_lq_interval_key, get_resend_key)
from constants.GATEWAY import HEARTBEAT_INTERVAL, SLEEP_HEARTBEAT_INTERVAL


"""Some methods widely used in gateway.
"""

def append_gw_request(request, connection, channel, exchange, gw_binding):
    """Append request to GW.
    """
    #BIG NOTE: json.dumps may be change the python object's struck. :
    # For list, and tuple in python will become array in json. (ip,port)-->[ip,port]
    message = json.dumps(request)
    # make message not persistent
    properties = pika.BasicProperties(delivery_mode=1,)
    channel.basic_publish(exchange=exchange,
                          routing_key=gw_binding,
                          body=message,
                          properties=properties) 

def append_si_request(request, connection, channel, exchange, si_binding):
    """Append request to SI.
    """
    request = dict({"packet":request})
    message = json.dumps(request)
    # make message not persistent
    properties = pika.BasicProperties(delivery_mode=1,)
    channel.basic_publish(exchange=exchange,
                          routing_key=si_binding,
                          body=message,
                          properties=properties)

def update_terminal_status(redis, dev_id, address, is_sleep=False):
    """Keep the latest address of termianl in redis.
    """
    terminal_status_key = get_terminal_address_key(dev_id)
    lq_interval_key = get_lq_interval_key(dev_id)
    is_lq = redis.getvalue(lq_interval_key)
    if is_sleep:
        redis.delete(lq_interval_key)
        is_lq = False

    if is_lq and not is_sleep:
        redis.setvalue(terminal_status_key, address, 10 * HEARTBEAT_INTERVAL)
    else:
        redis.setvalue(terminal_status_key, address, (1 * SLEEP_HEARTBEAT_INTERVAL + 300))

def get_resend_flag(redis, tid, timestamp, command): 
    """Get resend flag.
    """
    resend_key = get_resend_key(tid, timestamp, command)
    resend_flag = redis.getvalue(resend_key)
    return resend_key, resend_flag
