#!/bin/bash

# Allow tsx to sudo without password
echo "tsx ALL=NOPASSWD: ALL" > /etc/sudoers.d/tsx

# Setup R APT repository - https://www.digitalocean.com/community/tutorials/how-to-install-r-on-ubuntu-18-04
apt-get install -y software-properties-common gnupg
apt-key adv --keyserver keyserver.ubuntu.com --recv-keys E298A3A825C0D65DFD57CBB651716619E084DAB9
add-apt-repository 'deb https://cloud.r-project.org/bin/linux/ubuntu bionic-cran35/'

apt-get update
apt-get install -y nginx mysql-server python python-pip virtualenv r-base git

cd ~tsx

sudo -u tsx git clone https://github.com/nesp-tsr3-1/tsx.git

cd tsx

sudo -u tsx python setup/download_sample_data.py

setup/setup-database.sh

# Setup environment
sudo -u tsx virtualenv env
sudo -u tsx source env/bin/activate
sudo -u tsx pip install -r requirements.txt
