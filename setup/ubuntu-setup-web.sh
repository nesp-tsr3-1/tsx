#!/bin/bash

# Make sure apt-get doesn't ask questions
export DEBIAN_FRONTEND=noninteractive

# Setup
apt-get install -y apache2
apt-get install -y libmysqlclient-dev libgeos-dev
apt install -y libssl1.0-dev nodejs-dev node-gyp npm

# Set up phpmyadmin
apt install -y phpmyadmin php-mbstring php-gettext
sudo ln -s /usr/share/phpmyadmin /var/www/html
sudo service apache2 restart

# Install tsx web service
sudo -u tsx cd ~/tsx && python setup.py install && sudo cp etc/init.d/tsxapi /etc/init.d/
/etc/init.d/tsxapi start
