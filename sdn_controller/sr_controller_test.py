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

class parameters(object):
	in_port = 0
	out_port = 0
	ipv6_dst = 0
	sr_mac = 0
	dst_mac = 0
	segs = []

	def __init__(self, in_port = 0, out_port = 0, ipv6_dst = 0, sr_mac = 0, dst_mac = 0, segs = None):
		self.in_port = in_port
		self.out_port = out_port
		self.ipv6_dst = ipv6_dst
		self.sr_mac = sr_mac
		self.dst_mac = dst_mac
		self.segs = segs

	def print_me(self):
		print "========parameters========="
		print "in_port=%s,out_port=%s,ipv6_dst=%s,sr_mac=%s,dst_mac=%s,segs=%s" % (self.in_port, self.out_port, self.ipv6_dst, self.sr_mac, self.dst_mac, self.segs)

class SMORE_controller(app_manager.RyuApp):
	IPV6_TYPE = 0x86DD	
	SRV6_PORT = 5
	OVS_ADDR = {	"0":"127.0.0.1",
			"1":"155.98.39.68"
			}
	OVS_INPORT = { "0":1,
			"1":1
			}
	OVS_OUTPORT = { "0":2,
			"1":2
			}
	OVS_IPV6_DST = { "0":"2001::209:204:23ff:feb7:2660", #n6's net2
			 "1":"2001::203:204:23ff:feb7:1a0a" #n0's net1
			}
	OVS_SR_MAC = { "0":"00:04:23:b7:12:da",	#n2's neta mac
			 "1":"00:04:23:b7:19:71"	#n3's nete mac
			}
	OVS_DST_MAC = { 
			 "0":"00:04:23:b7:1a:0a",	#n0's net1 mac
			"1":"00:04:23:b7:26:60"        #n6's net2 mac
			}

	#2->4->3, 3->4->2
	OVS_SEGS = { "0":["2001::204:204:23ff:feb7:12da", "2001::206:204:23ff:fea8:da63", "2001::207:204:23ff:feb7:2101"],	#n2'neta, n4's netc, n3's netd
			 "1":["2001::208:204:23ff:feb7:1971","2001::207:204:23ff:fea8:da62", "2001::206:204:23ff:feb7:1311"] #n3's nete, n4's netd, n2's netc
			}

	#2->3, 3->2
	#OVS_SEGS = { "0":["2001::204:204:23ff:feb7:12da", "2001::205:204:23ff:feb7:2100"],	#n2'neta, n3's netb
	#		 "1":["2001::208:204:23ff:feb7:1971","2001::205:204:23ff:feb7:12db"] #n3's nete, n2's netb
	#		}






	def get_parameters(self, ovs_address):
		ovs = "1"
		for i in self.OVS_ADDR:
			if self.OVS_ADDR[i] == ovs_address:
				ovs = "%s" % i
				break
		return parameters(in_port = self.OVS_INPORT[i], out_port = self.OVS_OUTPORT[i], ipv6_dst = self.OVS_IPV6_DST[i], sr_mac = self.OVS_SR_MAC[i], dst_mac = self.OVS_DST_MAC[i], segs = self.OVS_SEGS[i])

	def _add_flow(self, datapath, priority, match, actions):
	      ofproto = datapath.ofproto
	      parser = datapath.ofproto_parser

	      inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
						   actions)]

	      mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
				      match=match, instructions=inst)
	      datapath.send_msg(mod)

	def _push_flows_sr_ryu(self, parser, datapath, parameters):
	    '''
		$OVS_OFCTL add-flow br0 in_port=$NETA,priority=2,eth_type=$IPV6_TYPE,ipv6_dst="2001::211:43ff:fee4:9720",actions="set_field:2001::204:23ff:feb7:17be->ipv6_dst",output:$ENCAP
		$OVS_OFCTL add-flow br0 in_port=$ENCAP,eth_type=$IPV6_TYPE,ipv6_dst="2001::204:23ff:feb7:17be",priority=2,actions=mod_dl_dst:"00:04:23:b7:17:be",output:$NETB	
	    '''

	    print "******Pushing SR flows on: %s ....." % datapath.address[0]
	    parameters.print_me()

	    #1
	    match = parser.OFPMatch(in_port=parameters.in_port,eth_type=SMORE_controller.IPV6_TYPE,ipv6_dst="%s"%parameters.ipv6_dst)
	    actions = []
	    for segment in parameters.segs:
            	actions.append(parser.OFPActionSetField(ipv6_dst=segment))
	    actions.append(parser.OFPActionOutput(SMORE_controller.SRV6_PORT))
	    self._add_flow(datapath,3,match,actions)

	    #2
	    match = parser.OFPMatch(in_port=SMORE_controller.SRV6_PORT)
	    actions = []
	    actions.append(parser.OFPActionSetField(eth_dst=parameters.sr_mac))
	    actions.append(parser.OFPActionOutput(parameters.out_port))
	    self._add_flow(datapath,3,match,actions)

	    print "******Pushing returning dst flow on: %s ....." % datapath.address[0] #returning, in the out_port, out the in_port
	    match = parser.OFPMatch(in_port=parameters.out_port)
	    actions = []
	    actions.append(parser.OFPActionSetField(eth_dst=parameters.dst_mac))
	    actions.append(parser.OFPActionOutput(parameters.in_port))
	    self._add_flow(datapath,3,match,actions)



	
	    '''
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
            '''
	

	def __init__(self, *args, **kwargs):
		super(SMORE_controller, self).__init__(args, kwargs)
		print "Controller started."

	def __del__(self):
		thread.exit()

	@set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
	def switch_features_handler(self, ev):
		datapath = ev.msg.datapath
		ofproto = datapath.ofproto
		parser = datapath.ofproto_parser
		ovs_address = datapath.address[0]
		parameters = self.get_parameters(ovs_address)
		self._push_flows_sr_ryu(parser, datapath, parameters)

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
