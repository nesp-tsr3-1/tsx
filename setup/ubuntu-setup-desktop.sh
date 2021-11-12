#!/bin/bash

# Run as root
export DEBIAN_FRONTEND=noninteractive

# Minimal desktop environment - https://askubuntu.com/a/954271/521491
apt-get update
sudo apt install -y xfce4 --no-install-recommends
sudo apt install -y sddm xfce4-terminal

# R studio
wget https://download1.rstudio.org/desktop/bionic/amd64/rstudio-2021.09.1-372-amd64.deb
apt-get install -y gdebi-core
gdebi -n rstudio-2021.09.1-372-amd64.deb
rm rstudio-2021.09.1-372-amd64.deb

# Autologin:
cat > /etc/sddm.conf <<EOF
[Autologin]
Relogin=false
User=tsx
Session=xfce
EOF

# Don't require password to login or unlock
usermod -a -G nopasswdlogin tsx

# Auto start terminal
sudo -u tsx mkdir -p ~tsx/.config/autostart
sudo -u tsx touch ~tsx/.config/autostart/app.desktop
cat > ~tsx/.config/autostart/app.desktop <<EOF
[Desktop Entry]
Type=Application
Name=Terminal
Exec=xfce4-terminal
StartupNotify=false
Terminal=false
EOF

# Screen resolution
echo "xrandr -s 1280x768" >> /etc/X11/Xsession.d/45custom_xrandr-settings

# Auto enter tsx and enable environment
cat >> ~tsx/.bashrc <<EOF
# Enter TSX directory and activate Python virtual environment
cd ~/tsx
source env/bin/activate
jupyter/run.sh

EOF
