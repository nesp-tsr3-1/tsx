#!/bin/bash

# Allow tsx to sudo without password
echo "tsx ALL=NOPASSWD: ALL" > /etc/sudoers.d/tsx

# Make sure apt-get doesn't ask questions
export DEBIAN_FRONTEND=noninteractive

# Autoconfigure host-only network
cat >> /etc/netplan/01-netcfg.yaml <<EOF
    enp0s8:
      dhcp4: yes
EOF

# Set hostname
hostnamectl set-hostname tsx

# Setup R APT repository - https://www.digitalocean.com/community/tutorials/how-to-install-r-on-ubuntu-18-04
apt-get install -y software-properties-common gnupg
apt-key adv --keyserver keyserver.ubuntu.com --recv-keys E298A3A825C0D65DFD57CBB651716619E084DAB9
add-apt-repository 'deb https://cloud.r-project.org/bin/linux/ubuntu bionic-cran35/'

apt-get update

apt-get install -y mysql-server python python-pip virtualenv r-base git samba libxslt1-dev

# For some reason I seem to have to install these one by one
apt-get install -y libssl-dev
apt-get install -y libgit2-dev
apt-get install -y libcurl4-openssl-dev

# Install R packages
R --no-save <<EOF
install.packages("devtools")
library(devtools)
install.packages("ggplot2")
install_github("nesp-tsr3-1/rlpi", dependencies=TRUE)
EOF

cd ~tsx

sudo -u tsx git clone https://github.com/nesp-tsr3-1/tsx.git

cd tsx

sudo -u tsx cp tsx.conf.example tsx.conf

sudo -u tsx python setup/download_sample_data.py

setup/setup-database.sh
sudo mysql tsx < sample-data/seed.sql

# Autologin to MySQL as tsx
sudo -u tsx cat > ~tsx/.my.cnf <<EOF
[client]
user=tsx
password=tsx
EOF

# Setup environment
sudo -u tsx bash <<EOF
virtualenv -p python3 env
source env/bin/activate
pip install -r requirements.txt
EOF

# Configure Samba Share
cat >> /etc/samba/smb.conf <<EOF

security = share

[tsx]
  comment = TSX Shared Files
  path = /home/tsx
  read only = no
  browsable = yes
  valid users = tsx
EOF

(echo tsx; sleep 1; echo tsx) | sudo smbpasswd -a tsx
