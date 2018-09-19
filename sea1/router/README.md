This is the Ansible role for Wobscale's Seattle router, present on the Seattle Internet Exchange.

The supported version of Ansible is the version available in [OpenBSD Ports](https://www.openbsd.org/faq/ports/) for the release we are currently using. For [OpenBSD 6.3 ports](https://cloudflare.cdn.openbsd.org/pub/OpenBSD/6.3/packages/amd64/) that version is 2.4.3.0.

## Running Ansible

Run Ansible from the `sea1` directory (one above this README.md).

First, check your changes:

```plain
ansible-playbook -b --become-method=doas --check --diff router/playbook.yaml
```

Make your changes:

```plain
ansible-playbook -b --become-method=doas router/playbook.yaml
```
