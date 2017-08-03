#!/bin/bash


# ETH2 FOR ENODEB
# ETH4 FOR S-GW
ovs-vsctl add-br br0 
ovs-vsctl set-fail-mode br0 secure
ifconfig eth2 0.0.0.0
ifconfig eth3 0.0.0.0
ifconfig eth4 0.0.0.0

# ETH2 -> ENODEB
# ETH3 -> OFF1
# ETH4 -> SGW
ovs-vsctl add-port br0 eth2
ovs-vsctl add-port br0 eth3
ovs-vsctl add-port br0 eth4
ovs-vsctl set bridge br0 protocols=OpenFlow10,OpenFlow12,OpenFlow13

ovs-vsctl show
