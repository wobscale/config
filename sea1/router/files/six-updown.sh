#!/bin/ksh
set -e

if [ "$1" != "up" ] && [ "$1" != "down" ]; then
    echo "usage: $0 up|down [REASON]"
    exit 1
fi

for neighbor in $(grep 'neighbor ' /etc/bgpd.conf | awk '{ print $2 }' | grep -F -e '206.81.8' -e '2001:504:16:' | tail -r); do
    echo -n "bring $neighbor $1? "
    read -r prompt
    [[ "$prompt" = "y" ]] || exit 2
    ( set -x; bgpctl neighbor "$neighbor" "$1" )
done
