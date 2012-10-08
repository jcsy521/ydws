#!/bin/bash

# swith login.html
cd ./apps/uweb/templates/
rm -f login.html
ln -s 608_login.html login.html
cd ../../../

sed -i -e "s/--logging=warning/--mode=debug --logging=DEBUG/" ./conf/supervisord/services-available/*.conf

cd ./apps/
rm -rf sms
rm -rf uweb/static
rm -f uweb/templates/base.html
rm -rf lbmp_sender
ln -s sms.d/sms_bj sms
ln -s lbmp_sender.d/lbmp_sender_bj lbmp_sender
cd uweb/
ln -s static.d/static_bj static
cd templates/
ln -s base_bj.html base.html
cd ../../../
