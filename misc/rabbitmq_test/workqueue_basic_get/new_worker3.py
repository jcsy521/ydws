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

def get(block=True, timeout=None):
    """Remove and return an item from the queue. 

    :arg block: bool. If true, it will block until one message got. If False, None maybe be found.
    :arg timeout: int, in seconds.


    #NOTE: If nothing can be found from the queue, the following get through basic_get() method:
    <Basic.GetEmpty(['cluster_id='])> None None

    """
    def _get():            
        method, header, body = channel.basic_get(queue='get')
        if method.NAME == 'Basic.GetEmpty':
            pass            
        else:
            channel.basic_ack(delivery_tag=method.delivery_tag)

        return body

    if block:
        if timeout:
            pass
        else:
            timeout = 60*10 #TODO: 10 minutes.
    
        _start_time = int(time.time())

        while True:
            time.sleep(1)
            _end_time = int(time.time())
            if (_end_time - _start_time) >= timeout:
                return _get()

            body = _get()
            if not body:
                continue                              
            else:
                return body 
    else:
        return _get()

if __name__ == '__main__':

    data = get()
    print '----data', data
