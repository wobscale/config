## Adding an IP Addy mapping

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
$ doas vim /etc/dhcpd.conf

# Respect the existing format. Mimic it. Love it. TODO, document it and ansible it.

# Validate. No ip or mac should be duplicated. Ever. Feel free to do a `grep -E "\d+.\d+.\d+.\d+" | uniq -c` type magic (note: totally untested one-liner for that file)

$ doas /etc/rc.d/dhcpd check # Service is running
$ doas /etc/rc.d/dhcpd restart
$ doas /etc/rc.d/dhcpd check # Service is running
$ sleep 3
$ doas /etc/rc.d/dhcpd check # Service is running

# Fuckit shipit

```

