#!/usr/bin/env python
#coding=utf8
import pika
import sys
 
connection = pika.BlockingConnection(pika.ConnectionParameters(
               'localhost'))
def test():
    print 'come into test'

connection.set_backpressure_multiplier(0)
connection.add_backpressure_callback(test)

channel = connection.channel()
 
#channel.queue_declare(queue='hello')
channel.queue_declare(queue='get')
# delete a queue.
#channel.queue_delete(queue='get')
#
message = ' '.join(sys.argv[1:]) or "Hello World!"
#message = 'jiaxiaolei'*100
#message = 'jiaxiaolei'*1000000000
 
channel.basic_publish(exchange='', 
                      routing_key='get', 
                      body=message)
print " [x] Sent %r" % (message,)
#
##while True:
##    message = ' '.join(sys.argv[1:]) or "Hello World!"
##    #message = 'jiaxiaolei'*100
##    #message = 'jiaxiaolei'*1000000000
##     
##    channel.basic_publish(exchange='', 
##                          routing_key='get', 
##                          body=message)
##    print " [x] Sent %r" % (message,)
connection.close()
