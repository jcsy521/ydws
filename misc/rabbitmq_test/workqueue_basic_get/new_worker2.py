import pika
import time

#connection = pika.BlockingConnection()
connection = pika.BlockingConnection(pika.ConnectionParameters(
               'localhost'))

def test():
    print 'come into test'

connection.set_backpressure_multiplier(0)
connection.add_backpressure_callback(test)

channel = connection.channel()

connection.set_backpressure_multiplier(2)

# get one item.
method_frame, header_frame, body = channel.basic_get(queue='get')
print 'all', method_frame, header_frame, body

if method_frame:
    if method_frame.NAME == 'Basic.GetEmpty':
        #print 'empty'
        time.sleep(1)
    else:
        print 'data', method_frame, header_frame, body
        # remove the item in queue.
        #channel.basic_ack(method_frame.delivery_tag)
else:
    print 'No message returned'


#while True:
#    method_frame, header_frame, body = channel.basic_get(queue='get')
#    print 'all', method_frame, header_frame, body
#    time.sleep(10)
#    if method_frame:
#        if method_frame.NAME == 'Basic.GetEmpty':
#            #print 'empty'
#            time.sleep(1)
#        else:
#            print 'data', method_frame, header_frame, body
#            channel.basic_ack(method_frame.delivery_tag)
#    else:
#        print 'No message returned'
print 'end'
