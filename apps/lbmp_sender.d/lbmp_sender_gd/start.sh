#!/bin/sh

me=$(dirname $0)
python2.6 -tt $me/server.py $1 $2 --mode=debug --logging=DEBUG 
#--conf=../../conf/global.conf --port=9000
