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
from ryu.ofproto import ofproto_v1_3 as ofproto
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from collections import defaultdict
import logging

LOG = logging.getLogger('ryu.app.SR_flows_mgmt')
LOG.setLevel(logging.DEBUG)

class SR_flows_mgmt(object):
  dpid_to_datapath = {}
  MATCH_FIELDS = {
	'in_port' : 'int',
	'ipv6_dst' : 'str', 
	'eth_type' : 'hex',
	'ipv6_src' : 'str',
	'eth_dst' : 'str',
	'eth_src' : 'str',
	'dl_src' : 'str',
	'dl_dst' : 'str',
	'out_port' : 'int'
  }

  def _del_flows(self, datapath):
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

      LOG.debug("Deleting all flow entries in table %s of OVS %s" % (table_id, datapath.address[0]))
      datapath.send_msg(flow_mod)

  def _delete_flow(self,datapath, priority, match):
      instructions = []
      flow_mod = datapath.ofproto_parser.OFPFlowMod(
            datapath,
            priority=priority,
            out_port=1,
            out_group=ofproto.OFPG_ANY,
            command=datapath.ofproto.OFPFC_DELETE_STRICT,
            match=match)
      datapath.send_msg(flow_mod)



  def _add_flow(self, datapath, priority, match, actions):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
               actions)]

        mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
              match=match, instructions=inst)
        datapath.send_msg(mod)

  def _get_datapath_from_dpid(self, dpid):
    dpid = int(dpid)
    if dpid in self.dpid_to_datapath:
    	return self.dpid_to_datapath[dpid], self.dpid_to_datapath[dpid].ofproto_parser
    return None, None


  @staticmethod
  def set_dpid_to_datapath(dpid_to_datapath):
  	SR_flows_mgmt.dpid_to_datapath = dpid_to_datapath

  def __init__(self, *args, **kwargs):
    super(SR_flows_mgmt, self).__init__(*args, **kwargs)

  def _casting(self, value, t):
	import importlib
	if t == "hex":
		return int(value, 16)

	try:
		module = importlib.import_module('__builtin__')
		cls = getattr(module, t)
	except AttributeError:
		return None
	return cls(value)
 
  def _generate_ipv6(self, ipv6_str):
	if "/" not in ipv6_str:
		return ipv6_str
	ipv6_addr = ipv6_str.split("/")[0]
	prefix_count = int(ipv6_str.split("/")[1])
	if prefix_count > 128:
		LOG.error("Invalid ipv6 address %s" % ipv6_str)
		return None
	if prefix_count == 128:
		return (ipv6_addr, "ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff")
	prefix = ""
	for i in range(1, prefix_count/4+1):
		prefix += "f"
		if i % 4 == 0 and i > 0:
			prefix += ":"
	if prefix[-1:] == ":":
		prefix += ":"
	else:
		prefix += "::"
	return (ipv6_addr, prefix)

	
  def _construct_match_args_list(self, match):
    ret = {}
    #ipv6_src=('2001:db8:bd05:1d2:288a:1fc0:1:10ee',
    #             'ffff:ffff:ffff:ffff::'),
    for key in match:
	if key in self.MATCH_FIELDS:
		if match[key] == None:
			continue
		if key == "ipv6_dst": #especially handle ipv6 with prefix
			ipv6_dst = self._generate_ipv6(match[key])
			ret[key] = ipv6_dst
			continue
		ret[key] = self._casting(match[key], self.MATCH_FIELDS[key])
		if ret[key] == None:
			LOG.error("Can't cast match's field %s to type %s" % (key, self.MATCH_FIELDS[key]))
	else:
		LOG.warn("Field %s is not defined" % key)
    return ret
	

  def _construct_match(self, parser, match):
    args = self._construct_match_args_list(match)
    m = parser.OFPMatch(**args)
    return m

  def _construct_actions(self, parser, actions):
    a = []
    for segment in actions['ipv6_dst']:
        a.append(parser.OFPActionSetField(ipv6_dst=segment))
    #list of SetField parameters https://github.com/faucetsdn/faucet/blob/master/faucet/valve_of.py
    for x in actions:
	if x == "mod_dl_dst" and actions[x]:
        	a.append(parser.OFPActionSetField(eth_dst=actions['mod_dl_dst']))
    a.append(parser.OFPActionOutput(int(actions['output'])))
    return a



###############################
#NORTHBOUND API implementations
################################
  def insert_single_flow(self, dpid, priority, match, actions):
    datapath, parser = self._get_datapath_from_dpid(dpid)
    if not datapath:
      LOG.error("Could not find datapth from dpid %s" % dpid)
      return 1

    m = self._construct_match(parser, match)
    a = self._construct_actions(parser, actions)

    LOG.debug("insert_single_flow (match, priority,action, datapath)=(%s,%s,%s,%s)" % (m, priority, a, datapath))
    self._add_flow(datapath,priority,m,a)
    return 0

  def delete_single_flow(self, dpid, priority, match):
    LOG.info("delete_single_flow, (dpid, match)=(%s, %s)" % (dpid, match))
    datapath, parser = self._get_datapath_from_dpid(dpid)
    if not datapath:
      LOG.error("Could not find datapth from dpid %s" % dpid)
      return 1

    m = self._construct_match(parser, match)
    LOG.debug("delete_single_flow (match, priority, datapath)=(%s,%s,%s)" % (m, priority, datapath))
    self._delete_flow(datapath,priority,m)
    return 0


    return

  def delete_all_flows(self, dpid):
    datapath, parser = self._get_datapath_from_dpid(dpid)
    self._del_flows(datapath)
    return 0
###########################################################
