#!/bin/bash

select conf in $(ls -d */) Exit; do
	if [ "$conf"x = "Exit"x ]; then
		echo "Bye."
		exit
	fi

	if [ -z "$conf" ]; then
		echo "Non exist configuration."
	else
		echo "switch to configuration: $conf"
		pushd .. > /dev/null
		rm -f conf
		ln -s conf.d/$conf conf
		if [ -f	./conf/update_conf.sh ]; then
			./conf/update_conf.sh
		else
			echo "WARNING: update_db_conf.sh not found."
		fi
		popd > /dev/null
		break
	fi
done
