packer {
  required_plugins {
    virtualbox = {
      version = ">= 0.0.1"
      source  = "github.com/hashicorp/virtualbox"
    }
  }
}

source "virtualbox-ovf" "tsx-web" {
  source_path            = "build/tsx/tsx.ova"
  output_directory       = "build/tsx-web"
  shutdown_command       = "sudo shutdown -P now"
  ssh_handshake_attempts = "20"
  ssh_pty                = true
  ssh_timeout            = "20m"
  ssh_username           = "tsx"
  ssh_password           = "tsx"
  format                 = "ova"
  vm_name                = "tsx-web"
  vboxmanage             = [
# Note: these following 4 lines only work if you have created a host-only network adapter
# in VirtualBox settings called vboxnet0. Note this is a *global* VirtualBox setting, not
# a per-machine setting
    [ "modifyvm", "{{.Name}}", "--nictype1", "virtio" ],

    [ "modifyvm", "{{.Name}}", "--memory", "2048" ],
    [ "modifyvm", "{{.Name}}", "--cpus", "1" ],
    [ "modifyvm", "{{.Name}}", "--rtcuseutc", "on" ],

    [ "modifyvm", "{{.Name}}", "--clipboard", "bidirectional" ]
  ]
}

build {
  sources = ["sources.virtualbox-ovf.tsx-web"]

  provisioner "shell" {
    execute_command = "echo 'tsx' | {{.Vars}} sudo -E -S bash '{{.Path}}'"
    scripts = [
      "../ubuntu-setup-web.sh",
      "scripts/minimize.sh",
      "scripts/cleanup.sh"
    ]
    expect_disconnect = true
  }
}
