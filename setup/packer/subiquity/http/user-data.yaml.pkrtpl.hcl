#cloud-config
autoinstall:
  version: 1
  early-commands:
    - sudo systemctl stop ssh
  locale: en_US
  refresh-installer:
    update: yes
  keyboard:
    layout: us
  storage:
    layout:
      name: lvm
  ssh:
    allow-pw: true
    install-server: yes
  user-data:
    disable_root: false
    users:
      -
        name: ${os_username}
        passwd: ${hashed_os_password}
        groups: [ adm, cdrom, dip, plugdev, lxd, sudo ]
        lock-passwd: false
        sudo: ALL=(ALL) NOPASSWD:ALL
        shell: /bin/bash
  packages:
    - qemu-guest-agent
  late-commands:
    - sudo systemctl start ssh
