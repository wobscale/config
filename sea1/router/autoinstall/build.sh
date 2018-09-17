#!/bin/bash -e
# SPDX-License-Identifier: GPL-3.0-only

# TODO: perhaps boot with a serial console and use expect to automatically type the autoinstall bits
# or perhaps: not

. vars

die() {
    echo "$1"
    exit 1
}

bold() {
    tput bold
    echo "$1"
    tput sgr0
}

vm_ssh() {
    echo "# $1" | grep -v "^# true$"
    ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=QUIET \
        -i tmp/id_ed25519 localhost -p 7922 -l root -t "$1"
}

boot_wait() {
    while ! vm_ssh true; do sleep 1; done
    sleep 10 # wait for init to settle
}

SCRIPTPATH="$(cd "$(dirname "$0")"; pwd -P)"
cd "$SCRIPTPATH"


## Download and run cdXY.iso
ISO_NAME="cd$(tr -d . <<<"$OPENBSD_RELEASE").iso"
[[ -e "$ISO_NAME.sha256" ]] || die "$ISO_NAME.sha256 missing"
[[ -e "$ISO_NAME" ]] || curl -O "https://$OPENBSD_MIRROR/$OPENBSD_PATH/amd64/$ISO_NAME"
sha256sum -c "$ISO_NAME.sha256"

mkdir -p tmp
rm -f system.img tmp/id_ed25519
truncate -s 100G system.img
ssh-keygen -t ed25519 -f tmp/id_ed25519 -N ''
bold "Type [A] [Enter] at the \"Welcome to OpenBSD\" prompt"
bold "Enter http://10.0.2.42/install.conf for the response file location"
qemu-system-x86_64 \
    -drive file=system.img,media=disk,format=raw \
    -drive file=$ISO_NAME,media=cdrom \
    -m 2048 -enable-kvm -smp 4 \
    -netdev user,id=mynet0,hostfwd=tcp:127.0.0.1:7922-:22,guestfwd=tcp:10.0.2.42:80-cmd:$SCRIPTPATH/serve_autoinstall.sh \
    -device e1000,netdev=mynet0 &

boot_wait
vm_ssh "syspatch"
vm_ssh "echo 'github.com,192.30.255.113 ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEAq2A7hRGmdnm9tUDbO9IDSwBK6TbQa+PXYPCPy6rbTrTtw7PHkccKrpp0yVhp5HdEIcKr6pLlVDBfOLX9QUsyCOV0wzfjIJNlGEYsdlLJizHhbn2mUjvSAHQqZETYP81eFzLQNnPHt4EVVUh7VfDESU84KezmD5QlWpXLmvU31/yMf+Se8xhHTvKSCZIFImWwoG6mbUoWf9nzpIoaSjB+weqqUUmpaaasXVal72J+UX2B+2RPW3RcT0eOzQgqlJL3RKrTJvdsjE3JEAvGq3lGHSZXy28G3skua2SmVi/w4yCE6gbODqnTWlg7+wC604ydGXA8VJiS5ap43JXiUFFAaQ==' >> .ssh/known_hosts"
vm_ssh "pkg_add ansible git"
vm_ssh "cd /usr/src; git clone https://github.com/wobscale/openbsd-sys.git sys"
vm_ssh "cd /usr/src/sys/arch/amd64/compile/GENERIC.MP; make obj; make config; make -j5; make install"
vm_ssh "git clone https://github.com/wobscale/config.git; cd config; sed -i -e 's/^edge.sea1.*$/& ansible_connection=local/' sea1/hosts"
### Commands that require hitting the internet must go above this *final* line
vm_ssh "cd config/sea1; ansible-playbook --diff router/playbook.yaml; shutdown -p now; exit"

wait
