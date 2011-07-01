#!/bin/bash

###CONFIG###
ip route add 202.51.56.0/21 via 202.51.56.108
LOCAL_IP="202.51.56.106"
############

ip rule add fwmark 1 lookup 100
ip route add local 0.0.0.0/0 dev br0 table 100 


echo 0 > /proc/sys/net/ipv4/conf/all/rp_filter
echo 1 > /proc/sys/net/ipv4/ip_forward

iptables -t mangle -N DIVERT
iptables -t mangle -A DIVERT -j MARK --set-mark 1
iptables -t mangle -A DIVERT -j ACCEPT
iptables -t mangle -A PREROUTING -p tcp -m socket -j LOG \
				--log-prefix '[SOCKET]'
iptables -t mangle -A PREROUTING -p tcp -m socket -j DIVERT
iptables -t mangle -A PREROUTING -d $LOCAL_IP -j DIVERT
iptables -t mangle -A PREROUTING -p tcp --dport 80 -j LOG \
				--log-prefix '[TPROXY]'
iptables -t mangle -A PREROUTING -p tcp --dport 80 -j TPROXY \
				--tproxy-mark 0x1/0x1 --on-port 3129

ebtables -t broute -A BROUTING -i eth1 -p 0x0800 \
	--ip-proto tcp --ip-dport 80 -j redirect --redirect-target DROP

ebtables -t broute -A BROUTING -i eth0 -p 0x0800 \
	--ip-proto tcp --ip-sport 80 -j redirect --redirect-target DROP

cd /proc/sys/net/bridge/
for i in *; do
	echo 0 > $i
done
unset i
