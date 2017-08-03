#!/bin/bash



ovs-ofctl add-flow br0 in_port=1,action=push_mpls:0x8847,"set_field:10->mpls_label,set_field:20->mpls_label",output=2
