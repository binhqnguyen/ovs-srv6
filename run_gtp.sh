#!/bin/bash

ovs-vsctl del-br br0

get_interface="perl /proj/PhantomNet/binh/simeca_scripts/get_interface_map.pl"
neta=$($get_interface | grep -w neta | awk '{print $3}')
netb=$($get_interface | grep -w netb | awk '{print $3}')


ovs-vsctl add-br br0
#ovs-vsctl set-fail-mode br0 standalone
ovs-vsctl set-fail-mode br0 secure
ifconfig $neta 0.0.0.0
ifconfig $netb 0.0.0.0

ovs-vsctl add-port br0 $neta
ovs-vsctl  add-port br0 $netb
ovs-vsctl set bridge br0 protocols=OpenFlow10,OpenFlow12,OpenFlow13


echo "===================================="
echo "ADDING SRV6 PORTS"
echo "===================================="
#ovs-vsctl add-port br0 gtp1 -- set interface gtp1 type=gtp options:remote_ip=flow options:in_key=flow options:dst_port=2152
#ovs-vsctl add-port br0 gtp2 -- set interface gtp2 type=gtp options:remote_ip=flow options:in_key=flow options:dst_port=2153
#ovs-vsctl add-port br0 gtp3 -- set interface gtp3 type=gtp options:remote_ip=flow options:local_ip=flow options:in_key=flow options:out_key=flow options:dst_port=2154

ovs-vsctl add-port br0 srv61 -- set interface srv61 type=srv6 options:remote_ip=flow options:in_key=flow options:dst_port=2152
ovs-vsctl add-port br0 srv62 -- set interface srv62 type=srv6 options:remote_ip=flow options:in_key=flow options:dst_port=2153
ovs-vsctl add-port br0 srv63 -- set interface srv63 type=srv6 options:remote_ip=flow options:local_ip=flow options:in_key=flow options:out_key=flow options:dst_port=2154


./utilities/ovs-vsctl set-controller br0 tcp:127.0.0.1
ovs-vsctl show
