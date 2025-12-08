#!/bin/bash

cd ~tsx

sudo -u tsx git clone https://github.com/nesp-tsr3-1/tsx.git

cd tsx

sudo -u tsx cp tsx.conf.example tsx.conf

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

pipenv sync
pip install jupyter jupyterlab
echo 'IRkernel::installspec()' | R --no-save
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
