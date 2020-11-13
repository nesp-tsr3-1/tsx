#!/bin/bash

# Run as root

# Minimal desktop environment - https://askubuntu.com/a/954271/521491
apt-get update
apt-get install -y lightdm lightdm-gtk-greeter lubuntu-default-settings lxappearance lxterminal virtualbox-guest-x11
apt-get install -y lxde  --no-install-recommends

# R studio
wget https://download1.rstudio.org/rstudio-xenial-1.1.463-amd64.deb
apt-get install -y gdebi-core
gdebi -n rstudio-xenial-1.1.463-amd64.deb
rm rstudio-xenial-1.1.463-amd64.deb

# Autologin:
cat > /etc/lightdm/lightdm.conf.d/10-autologin.conf <<EOF
[SeatDefaults]
autologin-user=tsx
autologin-user-timeout=0
user-session=Lubuntu
greeter-session=lightdm-gtk-greeter
EOF

# Don't require password to login or unlock
usermod -a -G nopasswdlogin tsx

# Auto start terminal
sudo -u tsx mkdir -p ~tsx/.config/lxsession/Lubuntu
sudo -u tsx touch ~tsx/.config/lxsession/Lubuntu/autostart
echo "@lxterminal" >> ~tsx/.config/lxsession/Lubuntu/autostart

# Screen resolution
echo "xrandr -s 1280x768" >> ~tsx/.config/lxsession/Lubuntu/autostart

# Auto enter tsx and enable environment
sudo -u tsx touch ~/tsx/start.sh
cat >> ~tsx/.bashrc <<EOF

# Enter TSX directory and activate Python virtual environment
cd ~/tsx
source env/bin/activate
jupyter/run.sh

EOF
