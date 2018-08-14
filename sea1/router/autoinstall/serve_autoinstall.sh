#!/bin/bash -e

. vars

SCRIPTPATH="$(cd "$(dirname "$0")"; pwd -P)"
cd "$SCRIPTPATH"

DATA=$(cat <<EOF
System hostname = edge
DNS domain name = sea1.wobscale.website
Password for root = *************
Public ssh key for root = $(cat tmp/id_ed25519.pub)
Allow root ssh login = prohibit-password
Do you expect to run the X Window System = no
Location of sets = http
HTTP Server = $OPENBSD_MIRROR
Server directory = $OPENBSD_PATH/amd64
Set name(s) = -all bsd.mp base* comp* man*
Are you *SURE* your install is complete without 'bsd' = yes
EOF
)

echo -en "HTTP/1.1 200 k\r\n"
echo -en "Content-Type: text/plain; charset=UTF-8\r\n"
echo -en "Content-Length: $((${#DATA}+1))\r\n\r\n"
echo "$DATA"
