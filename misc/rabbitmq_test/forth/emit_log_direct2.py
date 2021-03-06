#!/usr/bin/env python

import pika
import sys

host='drone-205'
connection = pika.AsyncoreConnection(pika.ConnectionParameters(
        host=host))
channel = connection.channel()

channel.exchange_declare(exchange='direct_logs',
                         type='direct')

channel.queue_declare(queue='log_test')

severity = sys.argv[1] if len(sys.argv) > 1 else 'info'
message = ' '.join(sys.argv[2:]) or 'Hello World!'
channel.basic_publish(exchange='direct_logs',
                      routing_key=severity,
                      body=message)

print " [x] Sent %r:%r" % (severity, message)
connection.close()
 


