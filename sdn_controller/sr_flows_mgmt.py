# Copyright (C) 2017 Binh Nguyen binh@cs.utah.edu.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

#!/usr/bin/python

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.controller import dpset
from ryu.app.wsgi import ControllerBase, WSGIApplication
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from collections import defaultdict

DEBUG = 0

#class SR_flows_mgmt(ControllerBase):
class SR_flows_mgmt(object):
  dpid_to_datapath = {}
  NUM_OF_OVS_SWITCHES = 1
  ARP_REQUEST_TYPE = 0x0806 
  IPV6_TYPE = 0x86DD
  PARAMETER_FILE = "/opt/net_info.sh"
  SRV6_PORT = 5
  OVS_ADDR = {}
  OVS_INPORT = { "0":1,
      "1":1
      }
  OVS_OUTPORT = { "0":2,
      "1":2
      }
  OVS_IPV6_DST = {}
  OVS_SR_MAC = {}
  OVS_DST_MAC = {}
  OVS_SEGS = defaultdict(list)
  IS_SHORTEST_PATH = "0"
  ALL_PARAMETERS = {}

  #OVS_IPV6_DST = { "0":"2001::208:204:23ff:feb7:2660", #n6's net2
  #    "1":"2001::204:204:23ff:feb7:1a0a" #n0's net1
  #   }
  #OVS_SR_MAC = { "0":"00:04:23:b7:12:da",  #n2's neta mac
  #    "1":"00:04:23:b7:19:71"  #n3's nete mac
  #   }
  #OVS_DST_MAC = { 
  #    "0":"00:04:23:b7:1a:0a", #n0's net1 mac
  #   "1":"00:04:23:b7:26:60"        #n6's net2 mac
  #   }

  #2->4->3, 3->4->2
  #OVS_SEGS = { "0":["2001::204:204:23ff:feb7:12da", "2001::206:204:23ff:fea8:da63", "2001::207:204:23ff:feb7:2101"], #n2'neta, n4's netc, n3's netd
  #    "1":["2001::208:204:23ff:feb7:1971","2001::207:204:23ff:fea8:da62", "2001::206:204:23ff:feb7:1311"] #n3's nete, n4's netd, n2's netc
  #   }

  #flows_mgmt2->3, 3->2
  #OVS_SEGS = { "0":["2001::204:204:23ff:feb7:12da", "2001::205:204:23ff:feb7:2100"], #n2'neta, n3's netb
  #    "1":["2001::208:204:23ff:feb7:1971","2001::205:204:23ff:feb7:12db"] #n3's nete, n2's netb
  #   }


  def del_flows(self, datapath):
      empty_match = datapath.ofproto_parser.OFPMatch()
      instructions = []
      table_id = 0 #remove flows in table 0 only!!
      ofproto = datapath.ofproto
      flow_mod = datapath.ofproto_parser.OFPFlowMod(datapath, 0, 0, table_id,
                                                    ofproto.OFPFC_DELETE, 0, 0,
                                                    1,
                                                    ofproto.OFPCML_NO_BUFFER,
                                                    ofproto.OFPP_ANY,
                                                    ofproto.OFPG_ANY, 0,
                                                    empty_match, instructions)

      print "[C] Deleting all flow entries in table %s of OVS %s" % (table_id, datapath.address[0])
      datapath.send_msg(flow_mod)


  def _extract_value(self, keyword, l):
    k = "%s="%keyword
    if k in l:
      return l.split("=")[1][1:-2]
    else:
      return None

  def fetch_parameters_from_file(self):
    for l in open(self.PARAMETER_FILE, "read").readlines():
      if self._extract_value("n1_pub", l):
        self.OVS_ADDR["0"] = self._extract_value("n1_pub", l)
      if self._extract_value("n5_pub", l):
        self.OVS_ADDR["1"] = self._extract_value("n5_pub", l)


      if self._extract_value("n6_2", l):
        self.OVS_IPV6_DST["0"] = self._extract_value("n6_2", l)
      if self._extract_value("n0_1", l):
        self.OVS_IPV6_DST["1"] = self._extract_value("n0_1", l)

      if self._extract_value("n2_a_mac", l):
        self.OVS_SR_MAC["0"] = self._extract_value("n2_a_mac", l)
      if self._extract_value("n3_e_mac", l):
        self.OVS_SR_MAC["1"] = self._extract_value("n3_e_mac", l)

      if self._extract_value("n0_1_mac", l):
        self.OVS_DST_MAC["0"] = self._extract_value("n0_1_mac", l)
      if self._extract_value("n6_2_mac", l):
        self.OVS_DST_MAC["1"] = self._extract_value("n6_2_mac", l)

      if self._extract_value("IS_SHORTEST_PATH",l):
        self.IS_SHORTEST_PATH = self._extract_value("IS_SHORTEST_PATH", l)

      if "#" not in l:
              [key, value] = l.split("=")
      self.ALL_PARAMETERS[key] = value[1:-2]

  def _construct_segments(self):
    if self.IS_SHORTEST_PATH == "1":
      #segments 2->3, 3->2
      self.OVS_SEGS["0"].append(self.ALL_PARAMETERS["n2_a"])
      self.OVS_SEGS["0"].append(self.ALL_PARAMETERS["n3_b"])

      self.OVS_SEGS["1"].append(self.ALL_PARAMETERS["n3_e"])
      self.OVS_SEGS["1"].append(self.ALL_PARAMETERS["n2_b"])
    else:
      #segments 2->4->3, 3->4->2
      self.OVS_SEGS["0"].append(self.ALL_PARAMETERS["n2_a"])
      self.OVS_SEGS["0"].append(self.ALL_PARAMETERS["n4_c"])
      self.OVS_SEGS["0"].append(self.ALL_PARAMETERS["n3_d"])

      self.OVS_SEGS["1"].append(self.ALL_PARAMETERS["n3_e"])
      self.OVS_SEGS["1"].append(self.ALL_PARAMETERS["n4_d"])
      self.OVS_SEGS["1"].append(self.ALL_PARAMETERS["n2_c"])

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

  def _get_datapath_from_dpid(self, dpid):
    for dpid in self.dpid_to_datapath:
      if self.dpid_to_datapath[dpid]:
        return self.dpid_to_datapath[dpid], self.dpid_to_datapath[dpid].ofproto_parser
    return None, None


  def _push_flows_sr_ryu(self, parser, datapath, parameters):
      	'''
    	$OVS_OFCTL add-flow br0 in_port=$NETA,priority=2,eth_type=$IPV6_TYPE,ipv6_dst="2001::211:43ff:fee4:9720",actions="set_field:2001::204:23ff:feb7:17be->ipv6_dst",output:$ENCAP
    	$OVS_OFCTL add-flow br0 in_port=$ENCAP,eth_type=$IPV6_TYPE,ipv6_dst="2001::204:23ff:feb7:17be",priority=2,actions=mod_dl_dst:"00:04:23:b7:17:be",output:$NETB 
      	'''

    	print "[C] Pushing SR flows on OVS: %s" % datapath.address[0]
      	if self.IS_SHORTEST_PATH == "1":
    		print "[C] Installing Segment Routing Rules: USING shortest path!"
      	else:
   		print "[C] Installing Segment Routing Rules: NOT USING shortest path!"
      	if DEBUG == 1:
    		parameters.print_me()

      	#1
      	match = parser.OFPMatch(in_port=parameters.in_port,eth_type=SR_flows_mgmt.IPV6_TYPE,ipv6_dst="%s"%parameters.ipv6_dst)
      	actions = []
      	for segment in parameters.segs:
              actions.append(parser.OFPActionSetField(ipv6_dst=segment))
      	actions.append(parser.OFPActionOutput(SR_flows_mgmt.SRV6_PORT))
      	self._add_flow(datapath,3,match,actions)

      	#2
      	match = parser.OFPMatch(in_port=SR_flows_mgmt.SRV6_PORT)
      	actions = []
      	actions.append(parser.OFPActionSetField(eth_dst=parameters.sr_mac))
      	actions.append(parser.OFPActionOutput(parameters.out_port))
      	self._add_flow(datapath,3,match,actions)

      	print "[C] Pushing bridging flows for all other IPV6 packets on OVS: %s" % datapath.address[0]
      	match = parser.OFPMatch(in_port=parameters.in_port,eth_type=SR_flows_mgmt.IPV6_TYPE)
      	actions = []
      	actions.append(parser.OFPActionOutput(parameters.out_port))
      	self._add_flow(datapath,0,match,actions) #lowest priority


      	match = parser.OFPMatch(in_port=parameters.out_port,eth_type=SR_flows_mgmt.IPV6_TYPE)
      	actions = []
      	actions.append(parser.OFPActionOutput(parameters.in_port))
      	self._add_flow(datapath,0,match,actions)  #lowest priority


  @staticmethod
  def set_dpid_to_datapath(dpid_to_datapath):
  	SR_flows_mgmt.dpid_to_datapath = dpid_to_datapath

  def __init__(self, *args, **kwargs):
    super(SR_flows_mgmt, self).__init__(*args, **kwargs)
    #self.dpid_to_datapath = kwargs['dpid_to_datapath']
    #self.fetch_parameters_from_file()
    #self._construct_segments()
    #self.del_flows(self.datapath)
    #if DEBUG == 1:
    #  print "Fetched information from file: %s" %self.PARAMETER_FILE
    #  print "OVS_IPV6_DST %s" % self.OVS_IPV6_DST
    #  print "OVS_SR_MAC %s" % self.OVS_SR_MAC
    #  print "OVS_DST_MAC %s" % self.OVS_DST_MAC
    #  print "OVS_SEGS %s" % self.OVS_SEGS
    #  print "OVS_ADDR %s" % self.OVS_ADDR
    #  print "IS_SHORTEST_PATH %s" % self.IS_SHORTEST_PATH
    #  print "ALL %s" % self.ALL_PARAMETERS
    #print "[C] SR flow manager started."


###############################
#NORTHBOUND API implementations
################################
  def insert_single_flow(self, dpid, priority, match, actions):
    datapath, parser = self._get_datapath_from_dpid(dpid)
    if not datapath:
      print "[ERROR] Could not find datapth from dpid %s" % dpid
      return

    #TODO: how to construct a match and actions here? potentially the fields could be "*" (empty).
    match = parser.OFPMatch(
      in_port=match['in_port'],
      eth_type=SR_flows_mgmt.IPV6_TYPE,
      ipv6_dst="%s"%match['nw_dst'],
      ipv6_src="%s"%match['nw_src'],
      eth_dst="%s"%match['dl_dst'],
      eth_src="%s"%match['dl_src']
    )
    a = []
    for segment in actions['ipv6_dst']:
        a.append(parser.OFPActionSetField(ipv6_dst=segment))
    a.append(parser.OFPActionOutput(actions['output']))

    self._add_flow(datapath,priority,match,actions)

    if DEBUG:
      print "[D]: insert_single_flow (match, priority,action, datapath)=(%s,%s,%s,%s)" % (match, priority, a, datapath)      

  def delete_single_flow(self, dpid, match):
    print "[C]: delete_single_flow, (dpid, match)=(%s, %s)" % (dpid, match)
    return

  def delete_all_flows(self, dpid):
    datapath, parser = self._get_datapath_from_dpid(dpid)
    self.del_flows(self, datapath)
    return
###########################################################
