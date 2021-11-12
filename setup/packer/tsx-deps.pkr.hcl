packer {
  required_plugins {
    virtualbox = {
      version = ">= 0.0.1"
      source  = "github.com/hashicorp/virtualbox"
    }
  }
}

source "virtualbox-ovf" "tsx-deps" {
  source_path            = "build/ubuntu2004/ubuntu2004.ova"
  output_directory       = "build/tsx-deps"
  shutdown_command       = "sudo shutdown -P now"
  ssh_handshake_attempts = "20"
  ssh_pty                = true
  ssh_timeout            = "20m"
  ssh_username           = "tsx"
  ssh_password           = "tsx"
  format                 = "ova"
  vm_name                = "tsx-deps"
  vboxmanage             = [
    [ "modifyvm", "{{.Name}}", "--memory", "2048" ],
    [ "modifyvm", "{{.Name}}", "--cpus", "1" ],
    [ "modifyvm", "{{.Name}}", "--rtcuseutc", "on" ]
  ]
}

build {
  sources = ["sources.virtualbox-ovf.tsx-deps"]

  provisioner "shell" {
    execute_command = "echo 'tsx' | {{.Vars}} sudo -E -S bash '{{.Path}}'"
    scripts = [ "../ubuntu-setup-tsx-deps.sh" ]
    expect_disconnect = true
  }
}
