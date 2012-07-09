#sudo aptitude install -y python-software-properties
#sudo aptitude install -y python-setuptools

#
## 1. install tornado
## sudo easy_install tornado
#sudo aptitude install -y curl
#curl -L "https://github.com/downloads/facebook/tornado/tornado-1.2.1.tar.gz" > tornado-1.2.1.tgz
#tar zxvf tornado-1.2.1.tgz
#cd tornado-1.2.1
#python setup.py build
#sudo python setup.py install
#cd ..
#

## 2. install MySQL-python
#sudo aptitude install -y libmysqlclient-dev
#sudo aptitude install -y python-dev
#sudo easy_install MySQL-python
#

## 3. install python-memcached
## sudo aptitude install python-memcache
#sudo easy_install python-memcached
#

## 4. install celery
#sudo aptitude install -y rabbitmq-server 
#sudo easy_install celery
#sudo rabbitmqctl delete_user guest
#sudo rabbitmqctl add_user celery celery 
#sudo rabbitmqctl add_vhost celeryhost 
#sudo rabbitmqctl set_permissions -p celeryhost celery ".*" ".*" ".*"
##2. create RabbitMQ user(http://www.rabbitmq.com/admin-guide.html)
##3. make sure hostname is available and not starts with numbers.
##4. config configcelery.py

## 5. install utilities
#sudo aptitude install -y libjpeg62-dev libfreetype6-dev
#sudo easy_install pil
#sudo easy_install python-dateutil
#sudo easy_install pycrypto
#sudo add-apt-repository "deb http://archive.canonical.com/ lucid partner"
#sudo aptitude update
#sudo aptitude install -y sun-java6-jdk

## 6.
#sudo aptitude install -y mysql-server mysql-client

# 
## 7 install supervisor
#sudo aptitude install -y supervisor

## 8. nginx
#sudo add-apt-repository ppa:nginx/stable
#sudo aptitude update
#sudo aptitude install -y nginx

## 9. keepalivecd
#sudo aptitude install -y keepalived
