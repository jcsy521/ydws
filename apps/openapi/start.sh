#!/bin/sh

me=$(dirname $0)
python -tt $me/server.py $1 $2 --logging=DEBUG 
