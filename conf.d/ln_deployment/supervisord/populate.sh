#!/bin/bash

BASE=$HOME/lbs/conf.d/ln_deployment/supervisord
TARGET=/etc/supervisor
LOG_DEST=/var/log/supervisor

declare -A services
services[web]='uweb sender eventer'
services[inter]='receiver sms xxtsyncer'
services[app]='admin celeryd'

function usage() 
{
    echo "Usage: `basename $0` {web|inter|app}"
}

function populate()
{
    cd $TARGET

    if [ ! -f supervisord.conf.bak ]
    then
	echo "back up old supervisord.conf"
	mv supervisord.conf supervisord.conf.bak
    fi

    echo "linking supervisord.conf..."
    ln -fs $BASE/supervisord.conf supervisord.conf

    if [ ! -d services-enabled ]
    then
	echo "create services-enabled..."
	mkdir services-enabled
    fi
    cd services-enabled
    rm -f *.conf

    for service in ${services[$1]}
    do
	echo "linking $service.conf"
	ln -fs $BASE/services-available/$service.conf $service.conf
	if [ ! -d $LOG_DEST/$service ]; then
		mkdir $LOG_DEST/$service
        if [ "$service" = "sms" ]; then
           mkdir $LOG_DEST/$service/pabb $LOG_DEST/$service/xxt 
        fi
	fi
    done
}

if [ $# -ne 1 -o -z "${services[$1]}" ]
then
    usage
    exit
fi

populate $1
echo "DONE."
