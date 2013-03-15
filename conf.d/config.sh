#!/bin/bash

# kernel
echo "config kernel."
sudo sh -c 'echo "1" > /proc/sys/kernel/randomize_va_space'
sudo sh -c 'echo "1" > /proc/sys/net/ipv4/conf/all/rp_filter'
sudo sh -c 'echo "0" > /proc/sys/net/ipv4/conf/all/accept_source_route'
sudo sh -c 'echo "0" > /proc/sys/net/ipv4/conf/default/accept_source_route'
sudo sh -c 'echo "1" > /proc/sys/net/ipv4/icmp_echo_ignore_broadcasts'
sudo sh -c 'echo "1" > /proc/sys/net/ipv4/icmp_ignore_bogus_error_responses'
sudo sh -c 'echo "1" > /proc/sys/net/ipv4/conf/all/log_martians'

# disable ipv6
echo "disable ipv6."
sudo sh -c 'echo "net.ipv6.conf.all.disable_ipv6 = 1" >> /etc/sysctl.conf'
sudo sh -c 'echo "net.ipv6.conf.default.disable_ipv6 = 1" >> /etc/sysctl.conf'
sudo sh -c 'echo "net.ipv6.conf.lo.disable_ipv6 = 1" >> /etc/sysctl.conf'
sudo sysctl -p

# ntpdate in crontab
echo "sync timezone from ntp.ubuntu.com every day."
cd /etc/cron.daily/
sudo touch ntp && sudo chmod 755 ntp
sudo sh -c 'echo "#!/bin/sh\n\nntpdate ntp.ubuntu.com" > ntp'
echo "Done ntp config."

# /etc/fstab
sudo sh -c 'echo "tmpfs\t/dev/shm\ttmpfs\tdefaults,noexec,nosuid\t0\t0" >> /etc/fstab'

# Blacklisting IPV6
sudo sh -c 'echo "blacklist ipv6" >> /etc/modprobe.d/blacklist'
echo "Check ipv6..."
ip a

