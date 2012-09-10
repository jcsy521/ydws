#!/bin/sh

TOP_GW=172.16.0.1

ETH0=172.16.3.0
ETH1=123.99.230.173

TRAC=10.0.0.250
TRAC_PORT=80
TRAC_OUT_PORT=8999

NAGIOS=172.16.3.4
NAGIOS_OUT_PORT=8998
NAGIOS_PORT=80

route add -host $TRAC gw $TOP_GW
#
## sysctl -w net.ipv4.ip_forward=1
echo 1 > /proc/sys/net/ipv4/ip_forward
#
## iptables -F
## iptables -X
## iptables -Z
#
### Drone-005:mysql
### 用DNAT作端口映射 
##iptables -t nat -A PREROUTING -d $ETH1 -p tcp --dport $MYSQL_OUT_PORT -j DNAT --to $WEB:$MYSQL_PORT
### 用SNAT作源地址转换（关键），以使回应包能正确返回 
##iptables -t nat -A POSTROUTING -d $WEB -p tcp --dport $MYSQL_PORT -j SNAT --to $ETH0
### 一些人经常忘了打开FORWARD链的相关端口，特此增加 
##iptables -A FORWARD -o eth0 -d $WEB -p tcp --dport $MYSQL_PORT -j ACCEPT 
##iptables -A FORWARD -i eth0 -s $WEB -p tcp --sport $MYSQL_PORT -m state --state ESTABLISHED -j ACCEPT 
##
##
## Trac
## 用DNAT作端口映射 
iptables -t nat -A PREROUTING -d $ETH1 -p tcp --dport $TRAC_OUT_PORT -j DNAT --to $TRAC:$TRAC_PORT
# 用SNAT作源地址转换（关键），以使回应包能正确返回 
iptables -t nat -A POSTROUTING -d $TRAC -p tcp --dport $TRAC_PORT -j SNAT --to $ETH0
# 一些人经常忘了打开FORWARD链的相关端口，特此增加 
iptables -A FORWARD -o eth0 -d $TRAC -p tcp --dport $TRAC_PORT -j ACCEPT 
iptables -A FORWARD -i eth0 -s $TRAC -p tcp --sport $TRAC_PORT -m state --state ESTABLISHED -j ACCEPT 

# nagios
iptables -t nat -A PREROUTING -d $ETH1 -p tcp --dport $NAGIOS_OUT_PORT -j DNAT --to $NAGIOS:$NAGIOS_PORT
iptables -t nat -A POSTROUTING -d $NAGIOS -p tcp --dport $NAGIOS_PORT -j SNAT --to $ETH0
iptables -A FORWARD -o eth0 -d $NAGIOS -p tcp --dport $NAGIOS_PORT -j ACCEPT 
iptables -A FORWARD -i eth0 -s $NAGIOS -p tcp --sport $NAGIOS_PORT -m state --state ESTABLISHED -j ACCEPT 
