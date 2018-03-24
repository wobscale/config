## Adding an IP Address mapping

### Prereqs

* You must have ssh access to the management network (bastion host)
* You must have ssh and doas access to the router
* You must have engaged the engineer oncall.

### Steps

#### Access the wobscale router

From the management network, you may access the router at 10.255.255.10 over ssh on port 22.

```
$ ssh 10.255.255.10
$ # Should be on da bsd
$ cp /etc/dhcpd.conf $HOME/dhcpd.conf
$ vim $HOME/dhcpd.conf
# do some editing
# Respect the existing format. Mimic it. Love it. TODO, document it and ansible it.

$ dhcpd -n -c $HOME/dhcpd.conf && echo $?
0

# Validate. No ip or mac should be duplicated. Ever. Feel free to do a `grep -E "\d+.\d+.\d+.\d+" | uniq -c` type magic (note: totally untested one-liner for that file)

$ doas mv $HOME/dhcpd.conf /etc/dhcpd.conf
$ doas /etc/rc.d/dhcpd check # Service is running
$ doas /etc/rc.d/dhcpd restart
$ doas /etc/rc.d/dhcpd check # Service is running
$ sleep 3
$ doas /etc/rc.d/dhcpd check # Service is running

# Fuckit shipit
```

