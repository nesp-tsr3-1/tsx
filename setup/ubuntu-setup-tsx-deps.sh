#!/bin/bash

set -e # Abort on error
set -x # Echo each command before running

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
apt-get update
apt-get install -y software-properties-common gnupg
apt-key adv --keyserver keyserver.ubuntu.com --recv-keys E298A3A825C0D65DFD57CBB651716619E084DAB9
add-apt-repository 'deb https://cloud.r-project.org/bin/linux/ubuntu bionic-cran35/'

apt-get update

apt-get install -y mysql-server python python-pip virtualenv r-base git samba libxslt1-dev

# Set MySQL default character encoding to utf8
sudo tee -a /etc/mysql/mysql.conf.d/encoding-utf8.cnf > /dev/null <<EOF
[mysqld]
collation-server = utf8_unicode_ci
init-connect='SET NAMES utf8'
character-set-server = utf8
EOF

sudo service mysql restart

# For some reason I seem to have to install these one by one
apt-get install -y libssl-dev
apt-get install -y libgit2-dev
#apt-get install -y libcurl4-openssl-dev # Note: This uninstall libgit2-dev because libgit2-dev is not compatible with it... it wants gnu_tls intead

# Install R packages
R --no-save <<EOF
install.packages("devtools")
library(devtools)
install.packages("ggplot2")
install_github("nesp-tsr3-1/rlpi", dependencies=TRUE)
install.packages("IRkernel")
install.packages("tidyverse")
install.packages("data.table")
EOF
