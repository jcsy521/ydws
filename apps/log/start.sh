#!/bin/sh
me=$(dirname $0) 
python2.6 -tt $me/server.py $1 --mode=debug --logging=DEBUG 
