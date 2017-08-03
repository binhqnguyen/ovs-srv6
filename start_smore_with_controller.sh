#!/bin/bash


ovs-vsctl del-br br0

get_interface="perl /opt/script_for_smore/get_interface_map.pl"
net_d=$($get_interface | grep -w net-d[[:blank:]] | awk '{print $3}')
net_d_mme=$($get_interface | grep -w net-d-mme | awk '{print $3}')
offload=$($get_interface | grep offload | awk '{print $3}')
controller_ip="127.0.0.1"

ovs-vsctl add-br br0 
ovs-vsctl set-fail-mode br0 secure
ifconfig $net_d 0.0.0.0
ifconfig $offload 0.0.0.0
ifconfig $net_d_mme 0.0.0.0

ovs-vsctl add-port br0 $net_d
ovs-vsctl add-port br0 $offload
ovs-vsctl add-port br0 $net_d_mme
ovs-vsctl set bridge br0 protocols=OpenFlow10,OpenFlow12,OpenFlow13

ovs-vsctl add-port br0 gtp1 -- set interface gtp1 type=gtp options:remote_ip=flow options:in_key=flow options:dst_port=2152
ovs-vsctl add-port br0 gtp2 -- set interface gtp2 type=gtp options:remote_ip=flow options:in_key=flow options:dst_port=2153
ovs-vsctl add-port br0 gtp3 -- set interface gtp3 type=gtp options:remote_ip=flow options:local_ip=flow options:in_key=flow options:out_key=flow options:dst_port=2154

ovs-vsctl set-controller br0 tcp:$controller_ip
ovs-vsctl show
