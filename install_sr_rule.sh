#!/bin/bash
OVS_OFCTL=./utilities/ovs-ofctl

NETA=1
NETB=2
ENCAP=5
# VARIABLES => OFF_MAC, ENODEB_MAC, ENODEB_TEID, SGW_TEID, SGW_MAC
OFF_MAC="00:04:23:b7:1b:e2"
OFF_IP="192.168.10.11"
IP_TYPE="0x0800"
IPV6_TYPE="0x08DD"
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

$OVS_OFCTL add-flow br0 in_port=$NETA,priority=2,eth_type=$IPV6_TYPE,actions=mod_dl_dst:$ENODEB_MAC,mod_dl_src=$SGW_MAC,"set_field:$ENODEB_TEID->tun_id","set_field:$ENODEB_IP->tun_dst","set_field:$SGW_IP->tun_src",output:$ENCAP
$OVS_OFCTL -v add-flow br0 in_port=$ENCAP,priority=2,actions=output:$NETB


$OVS_OFCTL dump-flows br0
