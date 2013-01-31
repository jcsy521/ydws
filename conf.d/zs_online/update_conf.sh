#!/bin/bash

# swith login.html
cd ./apps/uweb/templates/
rm -f login.html
ln -s 608_login.html login.html
cd ../../../

sed -i -e "s/--logging=warning/--mode=debug --logging=DEBUG/" ./conf/supervisord/services-available/*.conf

cd ./apps/
rm -f uweb/templates/base.html
rm -rf lbmp_sender
ln -s lbmp_sender.d/lbmp_sender_zs lbmp_sender
cd uweb/
cd templates/
ln -s base_bj.html base.html
cd ../../../
