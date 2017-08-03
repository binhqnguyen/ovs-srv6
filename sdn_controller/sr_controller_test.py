# Copyright (C) 2011 Nippon Telegraph and Telephone Corporation.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#	http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet

class SMORE_controller(app_manager.RyuApp):
	ev = None
	bridge = "tcp:127.0.0.1"
	ovs_ip = "127.0.0.1"
	ovs_port = 6633
	IPV6_TYPE = 0x86DD	
	SRV6_PORT = 5
	NETA_PORT = 1
	NETB_PORT = 2
	SEG1 = "2001::204:23ff:feb7:17be"
	SEG2 = "2001::204:23ff:feb7:17bf"
	SEG3 = "2001::204:23ff:feb7:17b0"
	SR_MAC = "00:04:23:b7:17:be"

	def _add_flow(self, datapath, priority, match, actions):
	      ofproto = datapath.ofproto
	      parser = datapath.ofproto_parser

	      inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
						   actions)]

	      mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
				      match=match, instructions=inst)
	      datapath.send_msg(mod)

	def _push_flows_sr_ryu(self, parser, datapath):
	    '''
		$OVS_OFCTL add-flow br0 in_port=$NETA,priority=2,eth_type=$IPV6_TYPE,ipv6_dst="2001::211:43ff:fee4:9720",actions="set_field:2001::204:23ff:feb7:17be->ipv6_dst",output:$ENCAP
		$OVS_OFCTL add-flow br0 in_port=$ENCAP,eth_type=$IPV6_TYPE,ipv6_dst="2001::204:23ff:feb7:17be",priority=2,actions=mod_dl_dst:"00:04:23:b7:17:be",output:$NETB	
	    '''

	    print "******Pushing SR flows ....." 

	    #1
	    match = parser.OFPMatch(in_port=SMORE_controller.NETA_PORT,eth_type=SMORE_controller.IPV6_TYPE,ipv6_dst="2001::211:43ff:fee4:9720")
	    actions = []
            actions.append(parser.OFPActionSetField(ipv6_dst=SMORE_controller.SEG1))
            actions.append(parser.OFPActionSetField(ipv6_dst=SMORE_controller.SEG2))
            actions.append(parser.OFPActionSetField(ipv6_dst=SMORE_controller.SEG3))
	    actions.append(parser.OFPActionOutput(SMORE_controller.SRV6_PORT))
	    self._add_flow(datapath,3,match,actions)

	    #2
	    match = parser.OFPMatch(in_port=SMORE_controller.SRV6_PORT)
	    actions = []
	    actions.append(parser.OFPActionSetField(eth_dst=SMORE_controller.SR_MAC))
	    actions.append(parser.OFPActionOutput(SMORE_controller.NETB_PORT))
	    self._add_flow(datapath,3,match,actions)

	

	def __init__(self, *args, **kwargs):
		super(SMORE_controller, self).__init__(args, kwargs)
		print "Controller started."

	def __del__(self):
		thread.exit()

	@set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
	def switch_features_handler(self, ev):
		self.ev = ev
		datapath = ev.msg.datapath
		ofproto = datapath.ofproto
		parser = datapath.ofproto_parser
		self._push_flows_sr_ryu(parser, datapath)

if __name__ == "__main__":
	#Testing Sniffer
	'''
	if len(sys.argv) != 6:
		print "Parameters: <net-d-enb interface> <offload-server interface> <net-d-mme interface> <ovs public IP> <ovs controller port>"
		exit(1)

	enb_port = str(sys.argv[1])
	offload_port = str(sys.argv[2])
	sgw_port = str(sys.argv[3])
	ovs_ip = str(sys.argv[4])
	ovs_port = str(sys.argv[5])
	bridge = "tcp:%s:%s" % (ovs_ip, ovs_port)

	smore = SMORE_Controller(bridge=bridge, ovs_ip=ovs_ip, enb_port=enb_inf, sgw_port=sgw_inf, offload_port=offload_inf)

	#create sniffer
	#sniffer = Sniffer(bridge, ovs_ip, enb_port, sgw_port, offload_port)
	'''
