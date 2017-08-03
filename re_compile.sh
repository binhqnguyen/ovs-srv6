#!/bin/bash

ovs-vsctl del-br br0
kill `cd /usr/local/var/run/openvswitch && cat ovsdb-server.pid ovs-vswitchd.pid`
modprobe -r openvswitch

modprobe gre
modprobe libcrc32c
#insmod /lib/modules/`uname -r`/extra/openvswitch.ko

insmod datapath/linux/openvswitch.ko
#mv /usr/local/etc/openvswitch/conf.db  /usr/local/etc/openvswitch/conf.db.bak
#ovsdb-tool create /usr/local/etc/openvswitch/conf.db vswitchd/vswitch.ovsschema
#
#
################# Startup ###########################
#ovsdb-server --remote=punix:/usr/local/var/run/openvswitch/db.sock \
#		      --remote=db:Open_vSwitch,Open_vSwitch,manager_options \
#		      --private-key=db:Open_vSwitch,SSL,private_key \
#		      --certificate=db:Open_vSwitch,SSL,certificate \
#		      --bootstrap-ca-cert=db:Open_vSwitch,SSL,ca_cert \
#		      --pidfile --detach
#
#		      
#ovs-vsctl --no-wait init
#ovs-vswitchd --pidfile --detach
