#!/bin/bash
OVS_OFCTL=./utilities/ovs-ofctl

NETA=1
NETB=2
ENCAP=5
# VARIABLES => OFF_MAC, ENODEB_MAC, ENODEB_TEID, SGW_TEID, SGW_MAC
OFF_MAC="00:04:23:b7:1b:e2"
OFF_IP="192.168.10.11"
IP_TYPE="0x0800"
IPV6_TYPE="0x86DD"
GTP_PORT=2152
ALICE_IP="192.168.3.100"
ARP_TYPE="0x0806"
ENODEB_MAC="00:04:23:b7:12:86"
ENODEB_IP="192.168.4.90"
ENODEB_TEID="0x00000015"
SGW_TEID="0x27588f09"
SGW_MAC="00:04:23:b7:18:2d"
SGW_IP="192.168.4.20"

$OVS_OFCTL del-flows br0 in_port=$NETA
$OVS_OFCTL del-flows br0 in_port=$NETB
$OVS_OFCTL del-flows br0 in_port=$ENCAP

#$OVS_OFCTL add-flow br0 in_port=$NETA,priority=2,eth_type=$IP_TYPE,actions=mod_dl_dst:$ENODEB_MAC,mod_dl_src=$SGW_MAC,"set_field:$ENODEB_TEID->tun_id","set_field:$ENODEB_IP->tun_dst","set_field:$SGW_IP->tun_src",output:$ENCAP
#$OVS_OFCTL add-flow br0 in_port=$ENCAP,priority=2,eth_type=$IP_TYPE,actions=output:$NETB

#$OVS_OFCTL add-flow br0 in_port=$NETA,priority=2,eth_type=$IPV6_TYPE,actions="set_field:fe80::3efd:feff:fe04:7dc0->ipv6_dst","set_field:fe80::3efd:feff:fe04:7dc1->ipv6_dst","set_field:fe80::3efd:feff:fe04:7dc2->ipv6_dst",output:$ENCAP
$OVS_OFCTL add-flow br0 in_port=$NETA,priority=2,eth_type=$IPV6_TYPE,ipv6_dst="2001::211:43ff:fee4:9720",actions="set_field:2001::204:23ff:feb7:17be->ipv6_dst",output:$ENCAP
#$OVS_OFCTL add-flow br0 in_port=$NETA,priority=2,eth_type=$IPV6_TYPE,ipv6_dst="2001::211:43ff:fee4:9716",actions="set_field:fe80::3efd:feff:fe04:7dc5->ipv6_dst","set_field:fe80::3efd:feff:fe04:7dc6->ipv6_dst","set_field:fe80::3efd:feff:fe04:7dc7->ipv6_dst",output:$ENCAP
#$OVS_OFCTL add-flow br0 in_port=$NETA,priority=2,eth_type=$IPV6_TYPE,actions="set_field:fe80::3efd:feff:fe04:7dc0->ipv6_dst","set_field:fe80::3efd:feff:fe04:7dc1->ipv6_dst",output:$ENCAP
#$OVS_OFCTL -v add-flow br0 in_port=$ENCAP,priority=2,actions=output:$NETB

#$OVS_OFCTL add-flow br0 in_port=$NETB,priority=2,eth_type=$IPV6_TYPE,actions="set_field:fe80::3efd:feff:fe04:7dc5->ipv6_dst","set_field:fe80::3efd:feff:fe04:7dc6->ipv6_dst","set_field:fe80::3efd:feff:fe04:7dc7->ipv6_dst",output:$ENCAP
$OVS_OFCTL add-flow br0 in_port=$ENCAP,eth_type=$IPV6_TYPE,ipv6_dst="2001::204:23ff:feb7:17be",priority=2,actions=mod_dl_dst:"00:04:23:b7:17:be",output:$NETB
#$OVS_OFCTL add-flow br0 in_port=$ENCAP,eth_type=$IPV6_TYPE,ipv6_dst="fe80::3efd:feff:fe04:7dc5",priority=3,actions=output:$NETB


$OVS_OFCTL dump-flows br0
