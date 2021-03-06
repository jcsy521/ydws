#!/usr/bin/env python
import pika
import sys

host='drone-205'
connection = pika.SelectConnection(pika.ConnectionParameters(
        host=host))
channel = connection.channel()


channel.exchange_declare(exchange='direct_logs',
                         type='direct')

channel.queue_declare(queue='log_test')

severities = sys.argv[1:]
if not severities:
    print >> sys.stderr, "Usage: %s [info] [warning] [error]" % \
                             (sys.argv[0],)

    sys.exit(1)

for severity in severities:
    channel.queue_bind(exchange='direct_logs',
                       queue='log_test',
                       routing_key=severity)

print ' [*] Waiting for logs. To exit press CTRL+C'

def callback(ch, method, properties, body):
    print " [x] %r:%r" % (method.routing_key, body,)

channel.basic_consume(callback,
                      queue='log_test',
                      no_ack=True)

channel.start_consuming()
 

