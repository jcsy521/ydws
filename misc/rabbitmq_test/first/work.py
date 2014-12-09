import pika
import time

#connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
connection = pika.BlockingConnection(pika.ConnectionParameters(host='drone-205'))
#connection = pika.BlockingConnection(pika.ConnectionParameters(host='192.168.1.105'))
channel = connection.channel()

channel.queue_declare(queue='si_requests_queue', durable=False)
print "[x] Waiting for message."

def callback(ch, method, properties, body):
    print '------body: %s, type: %s, repr: %s' % (body, type(body), repr(body))
    print "[x] Received %r" % body
    print 'sleep', body.count('.')
    time.sleep(body.count('.'))
    print '[x] Done'
    # 
    ch.basic_ack(delivery_tag=method.delivery_tag)

# This tells RabbitMQ not to give more than one message to a worker at a time
channel.basic_qos(prefetch_count=1)
channel.basic_consume(callback,
                      queue='si_requests_queue')

channel.start_consuming()
