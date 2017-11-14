#!/bin/bash

if [ $# -ne 3 ]; then
        echo "Usage: <sr_inport network name, eg, neta> <sr_outport network  name, eg, netb> <Controller'IP>"
        exit 1
else
        inport_name=$1
        outport_name=$2
        CONTROLLER_IP=$3
fi

ovs-vsctl del-br br0

get_interface="perl ./get_interface_map.pl"
sr_inport=$($get_interface | grep -w $inport_name | awk '{print $3}')
sr_outport=$($get_interface | grep -w $outport_name | awk '{print $3}')


ovs-vsctl add-br br0
#ovs-vsctl set-fail-mode br0 standalone
ovs-vsctl set-fail-mode br0 secure
host=$(hostname | awk -F"." '{print $1}')
if [ "$host" == "node1" ]; then
	ovs-vsctl set bridge br0 other-config:datapath-id=0000000000000002
fi
if [ "$host" == "node5" ]; then
	ovs-vsctl set bridge br0 other-config:datapath-id=0000000000000003
fi


ifconfig $sr_inport 0.0.0.0
ifconfig $sr_outport 0.0.0.0

ovs-vsctl add-port br0 $sr_inport
ovs-vsctl  add-port br0 $sr_outport
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


./utilities/ovs-vsctl set-controller br0 tcp:$CONTROLLER_IP
ovs-vsctl show
