#!/usr/bin/env python
#coding=utf8
import pika
import time
 
connection = pika.BlockingConnection(pika.ConnectionParameters(
               'localhost'))
channel = connection.channel()
 
#channel.queue_declare(queue='hello')

print 'channel', channel 
method_frame, header_frame, body = channel.basic_get('get')
print '-----------', method_frame, header_frame, body
if method_frame:
    print method_frame, header_frame, body
    channel.basic_ack(method_frame.delivery_tag)
else:
    print 'No message returned'

## for tst
#channel.queue_declare(queue='jiahello2',
#                      exclusive=True)
# 
#def callback(ch, method, properties, body):
#    print " [x] Received %r" % (body,)
#    #time.sleep(body.count('.'))
# 
#channel.basic_consume(callback, 
#                      queue='jiaxiaolei', 
#                      no_ack=True)
# 
#print ' [*] Waiting for messages. To exit press CTRL+C'
#channel.start_consuming()
