This is the host that's being built up to replace edge as the sea1 router.

The rule is: nobody makes a configuration that's not done as part of the Ansible playbooks.

Recommended (current) .ssh/config stanza:

```
Host waffle
    ProxyJump sea3-as11404.wobscale.website
    Hostname 10.50.7.121
```

This will change as the staging network becomes more like the real network.
