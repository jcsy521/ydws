#!/bin/bash
/usr/local/nginx/sbin/nginx
/opt/openfire/bin/openfire start
sleep 3
supervisorctl stop all
sleep 1
supervisorctl start all
