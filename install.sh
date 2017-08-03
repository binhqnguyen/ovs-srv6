#!/bin/bash



./boot.sh
./configure --with-linux=/lib/modules/`uname -r`/build
make  clean
make 
sudo make install
sudo make modules_install

sudo modprobe gre
sudo modprobe libcrc32c
#insmod /lib/modules/`uname -r`/extra/datapath/linux/openvswitch.ko
sudo insmod datapath/linux/openvswitch.ko
lsmod | grep openvswitch

# Initialize the configuration database using ovsdb-tool, e.g.:
#mkdir -p /usr/local/etc/openvswitch/
#ovsdb-tool create /usr/local/etc/openvswitch/conf.db vswitchd/vswitch.ovsschema
