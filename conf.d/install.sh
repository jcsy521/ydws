#!/bin/bash

# # svn
# sudo apt-get install -y subversion

# easy_install
sudo apt-get install -y python-setuptools

# aptitude
sudo apt-get install -y aptitude

# Add source
sudo sh -c 'echo "deb http://packages.dotdeb.org stable all" >> /etc/apt/sources.list'
sudo sh -c 'echo "deb-src http://packages.dotdeb.org stable all" >> /etc/apt/sources.list'
sudo sh -c 'echo "deb http://www.rabbitmq.com/debian/ testing main" >> /etc/apt/sources.list'
sudo sh -c 'echo "deb http://nginx.org/packages/ubuntu/ lucid nginx" >> /etc/apt/sources.list'
sudo sh -c 'echo "deb-src http://nginx.org/packages/ubuntu/ lucid nginx" >> /etc/apt/sources.list'
sudo sh -c 'echo "deb http://archive.canonical.com/ lucid partner" >> /etc/apt/sources.list'
sudo sh -c 'echo "deb http://us.archive.ubuntu.com/ubuntu/ hardy multiverse" >> /etc/apt/sources.list'
sudo apt-get update

# rabbitmq
wget -q -O - http://www.dotdeb.org/dotdeb.gpg | sudo apt-key add
wget http://www.rabbitmq.com/rabbitmq-signing-key-public.asc
sudo apt-key add rabbitmq-signing-key-public.asc

sudo add-apt-repository ppa:nginx/stable

# MySQL
sudo apt-get install mysql-server
sudo apt-get install mysql-client
mysql -uroot --default-character-set=utf8 -e 'GRANT ALL PRIVILEGES ON *.* TO pabb@"%" IDENTIFIED BY "pabb"'
# TODO
# config MySQL, then dump data from BJ 

# install MySQL-python
sudo aptitude install -y libmysqlclient-dev
sudo easy_install -U distribute
sudo easy_install MySQL-python

# tornado
wget https://github.com/downloads/facebook/tornado/tornado-2.4.1.tar.gz
tar zxvf tornado-2.4.1.tar.gz
cd tornado-2.4.1
python setup.py build
sudo python setup.py install
cd ../

wget -q -O - http://www.dotdeb.org/dotdeb.gpg | sudo apt-key add
sudo aptitude install -y redis-server
sudo easy_install redis

# install utilities
sudo aptitude install -y python-dev
sudo aptitude install -y libjpeg62-dev libfreetype6-dev
wget http://effbot.org/downloads/Imaging-1.1.7.tar.gz
tar zxvf Imaging-1.1.7.tar.gz
cd Imaging-1.1.7
# http://www.cnblogs.com/free--coder/archive/2012/09/12/2681361.html
# NOTE: \/usr\/lib\/x86_64-linux-gnu, This Path need check with command 
# sudo pkg-config --variable=libdir zlib && sudo pkg-config --variable=libdir freetype2
sed -i 's/ZLIB_ROOT = None/ZLIB_ROOT = "\/usr\/lib\/x86_64-linux-gnu"/g' setup.py
sed -i 's/FREETYPE_ROOT = None/FREETYPE_ROOT = "\/usr\/lib\/x86_64-linux-gnu"/g' setup.py
python setup.py build
sudo python setup.py install
cd ../
# sudo easy_install pil

# python-dateutil for timestamp
wget http://pypi.python.org/packages/source/p/python-dateutil/python-dateutil-2.1.tar.gz
tar zxvf python-dateutil-2.1.tar.gz
cd python-dateutil-2.1
python setup.py build
sudo python setup.py install
cd ../

# rabbitmq
wget http://www.rabbitmq.com/rabbitmq-signing-key-public.asc
sudo apt-key add rabbitmq-signing-key-public.asc
sudo apt-get install -y --force-yes rabbitmq-server
sudo easy_install 'pika==0.9.5'

# celery
wget http://pypi.python.org/packages/source/c/celery/celery-2.2.5.tar.gz#md5=d523c914a7c2761c70a4cc9058fdd6e8
tar xvfz celery-2.2.5.tar.gz 
cd celery-2.2.5
python setup.py build
python setup.py install 

sudo rabbitmqctl add_user celery celery
sudo rabbitmqctl add_vhost celeryhost
sudo rabbitmqctl set_permissions -p celeryhost celery ".*" ".*" ".*"

# supervisor
sudo apt-get install -y supervisor

# nginx
# http://wiki.nginx.org/Install
sudo apt-get install -y python-software-properties

sudo add-apt-repository ppa:nginx/stable
sudo apt-get install -y nginx
sudo apt-get install -y --force-yes nginx

# jdk just for push server
sudo apt-get install sun-java6-jdk 

# openfire
wget http://ichebao.net/openfire/openfire_3_7_1.tar.gz 
tar zxvf openfire_3_7_1.tar.gz
sudo cp -r openfire /opt/
cd /opt/openfire/bin
sudo ./openfire start

# jetty_acb
cd ~ 
wget http://ichebao.net/jetty_acb/jetty_acb.tar.gz
tar -zxvf jetty_acb.tar.gz

# keepalived
sudo aptitude install -y keepalived

sudo easy_install pyDes
