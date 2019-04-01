#!/bin/bash

# Allow tsx to sudo without password
echo "tsx ALL=NOPASSWD: ALL" > /etc/sudoers.d/tsx

# Set hostname
hostnamectl set-hostname tsx

# Setup R APT repository - https://www.digitalocean.com/community/tutorials/how-to-install-r-on-ubuntu-18-04
apt-get install -y software-properties-common gnupg
apt-key adv --keyserver keyserver.ubuntu.com --recv-keys E298A3A825C0D65DFD57CBB651716619E084DAB9
add-apt-repository 'deb https://cloud.r-project.org/bin/linux/ubuntu bionic-cran35/'

apt-get update
#apt-get install -y nginx mysql-server python python-pip virtualenv r-base git 
# phpmyadmin seems to like apache better
apt-get install -y apache2 mysql-server python python-pip virtualenv r-base git
apt-get install -y libmysqlclient-dev libgeos-dev
# For some reason I seem to have to install these one by one
apt-get install -y libssl-dev
apt-get install -y libgit2-dev
apt-get install -y libcurl4-openssl-dev

apt install -y libssl1.0-dev nodejs-dev node-gyp npm

# Install R packages
R --no-save <<EOF
install.packages("devtools")
library(devtools)
install.packages("ggplot2")
install_github("Zoological-Society-of-London/rlpi", dependencies=TRUE)
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
virtualenv env
source env/bin/activate
pip install -r requirements.txt
EOF

### set up phpmyadmin
sudo su -c "DEBIAN_FRONTEND=noninteractive apt install -y phpmyadmin php-mbstring php-gettext"
sudo ln -s /usr/share/phpmyadmin /var/www/html
sudo service apache2 restart

### install tsx
sudo -u tsx cd ~/tsx && python setup.py install && sudo cp etc/init.d/tsxapi /etc/init.d/
/etc/init.d/tsxapi start