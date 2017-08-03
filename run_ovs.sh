#!/bin/bash

./utilities/ovs-vsctl del-br br0
kill `cd /usr/local/var/run/openvswitch && cat ovsdb-server.pid ovs-vswitchd.pid`
#modprobe -r openvswitch

#modprobe gre
#modprobe libcrc32c
#insmod /opt/openvswitch/datapath/linux/openvswitch.ko
#insmod /opt/openvswitch.ko
################ Startup ###########################
./ovsdb/ovsdb-server --remote=punix:/usr/local/var/run/openvswitch/db.sock \
		      --remote=db:Open_vSwitch,Open_vSwitch,manager_options \
		      --private-key=db:Open_vSwitch,SSL,private_key \
		      --certificate=db:Open_vSwitch,SSL,certificate \
		      --bootstrap-ca-cert=db:Open_vSwitch,SSL,ca_cert \
		      --pidfile --detach

rm /var/log/ovs.log
		      
./utilities/ovs-vsctl --no-wait init
#ovs-vswitchd --pidfile --detach --log-file=ovs.log
./vswitchd/ovs-vswitchd --pidfile --detach --log-file=/var/log/ovs.log
./utilities/ovs-appctl vlog/set ANY:file:info

