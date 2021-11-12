packer {
  required_plugins {
    virtualbox = {
      version = ">= 0.0.1"
      source  = "github.com/hashicorp/virtualbox"
    }
  }
}

variable "os_username" {
  type = string
  default = "tsx"
  sensitive = true
}

variable "os_password" {
  type = string
  default = "tsx"
  sensitive = true
}

locals {
  hashed_os_password = bcrypt("${var.os_password}")
}

source "virtualbox-iso" "ubuntu-20-04-live-server" {
  boot_command =           [
        "<enter><enter><f6><esc><wait> ",
        "autoinstall ds=nocloud-net;seedfrom=http://{{ .HTTPIP }}:{{ .HTTPPort }}/",
        "<enter><wait>"
  ]
  boot_wait              = "5s"
  guest_os_type          = "ubuntu-64"
  http_content           = {
    "/meta-data" = file("subiquity/http/meta-data")
    "/user-data" = templatefile("subiquity/http/user-data.yaml.pkrtpl.hcl", {
      "os_username": "${var.os_username}"
      "hashed_os_password": "${local.hashed_os_password}"
    })
  }
  iso_url                = "https://releases.ubuntu.com/20.04/ubuntu-20.04.3-live-server-amd64.iso"
  iso_checksum           = "sha256:f8e3086f3cea0fb3fefb29937ab5ed9d19e767079633960ccb50e76153effc98"
  memory                 = 2048
  output_directory       = "build/ubuntu2004"
  shutdown_command       = "sudo shutdown -P now"
  ssh_handshake_attempts = "20"
  ssh_pty                = true
  ssh_timeout            = "20m"
  ssh_username           = "${var.os_username}"
  ssh_password           = "${var.os_password}"
  format                 = "ova"
  vm_name                = "ubuntu2004"
  vboxmanage             = [
    [ "modifyvm", "{{.Name}}", "--nictype1", "virtio" ],
    [ "modifyvm", "{{.Name}}", "--memory", "2048" ],
    [ "modifyvm", "{{.Name}}", "--cpus", "1" ]
  ]
}

build {
  sources = ["sources.virtualbox-iso.ubuntu-20-04-live-server"]

  provisioner "shell" {
    inline = [
      "while [ ! -f /var/lib/cloud/instance/boot-finished ]; do echo 'Waiting for cloud-init...'; sleep 1; done"
    ]
  }
}

