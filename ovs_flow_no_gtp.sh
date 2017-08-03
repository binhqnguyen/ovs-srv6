#!/bin/bash


if [ $# -lt 4 ]
then

        echo "Usage: $0 [port# of net_d interface] [port# of offload interface] [port# of net_d_mme interface] [port# of gtp1 interface]"
        exit
fi

net_d=$1
offload=$2
net_d_mme=$3
GTP=$4
DECAP=$(($GTP+1))
ENCAP=$(($GTP+2))

#
#Delete old flows on the bridge's interfaces.
#
ovs-ofctl del-flows br0 in_port=$net_d
ovs-ofctl del-flows br0 in_port=$net_d_mme
ovs-ofctl del-flows br0 in_port=$offload
ovs-ofctl del-flows br0 in_port=$GTP
ovs-ofctl del-flows br0 in_port=$ENCAP
ovs-ofctl del-flows br0 in_port=$DECAP

#
#Simple rules for turning the ovs node into a bridge:
#	1. In comming packets from enb node are forwarded to sgw-mme-sgsn node.
#	2. In comming packets from sgw-mme-sgsn node are forwarded to enb node.
#
ovs-ofctl add-flow br0 in_port=$net_d,priority=2,actions=output:$net_d_mme
ovs-ofctl add-flow br0 in_port=$net_d_mme,priority=2,actions=output:$net_d

if [ $? == 0 ]; then
	echo "Successfully installing bridge's forwarding rules:"
	ovs-ofctl dump-flows br0
	exit 0
else
	echo "Failed installing bridge's forwarding rules"
	exit 1
fi
