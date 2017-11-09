# Copyright (C) 2017 Binh Nguyen binh@cs.utah.edu.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
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
import logging
from webob import Response
from northbound_match import Match as Match
from northbound_actions import Actions as Actions
from sr_flows_mgmt import SR_flows_mgmt as SR_flows_mgmt
from structs import *
from ospfv3 import *
import json
import time

LOG = logging.getLogger('ryu.app.Te_controller')
LOG.setLevel(logging.DEBUG)

class Te_controller(ControllerBase):

	#Graph, static variable
	graph = G()

	def __init__(self, req, link, data, **config):
		super(Te_controller, self).__init__(req, link, data, **config)

	#REST API - Receive an ospf lsa from the router
	def receive_ospf_lsa(self, req, **_kwargs):
		data = req.json
		t = int(data['T'])
		if MSG_TYPES[t] == "LSUPD":
			v = data['V']['V']
			lsas = v['LSAS']
			graph = Te_controller.graph
			graph.clear_active_nbs()	#clear active neighbors to get new active neighbors
			graph.neighbor_last_refresh = time.time() #Start the refresh timer after receiving a LSUPD (likely link change detected)
	                #LOG.debug(graph.printNB())
			#LOG.debug("Received LSUDP=%s" % v)
			for k in lsas:
				lsa = lsas[k]
				t = int(lsa['T'])
				lsid = int(lsa['H']['LSID'])
				advrtr = int(lsa['H']['ADVRTR'])

				if LSAV3_TYPES[t] == "ROUTER":
					self._process_rtr_lsa(lsa['V'], lsid, advrtr)
				elif LSAV3_TYPES[t] == "NETWORK":
					self._process_network_lsa(lsa['V'], lsid, advrtr)
				elif LSAV3_TYPES[t] == "LINK LSA":
					self._process_link_lsa(lsa['V'], lsid, advrtr)
				elif LSAV3_TYPES[t] == "INTRA AREA PREFIX":
					self._process_intraareaprefix_lsa(lsa['V'], lsid, advrtr)
				else:
					LOG.warn("Received Unknown LSA, type:%s, lsid:%s, advrtr:%s" % (t, lsid, advrtr))
		elif MSG_TYPES[t] == "HELLO":
			v = data['V']['V']
			src_router_id = data['V']['RID']
			desig_router_id = v['DESIG']
			nbors = v['NBORS']
			self._process_hello(src_router_id, desig_router_id, nbors)

		return Response(status=500)
	
	#REST API - Return the topology graph 
	def get_topology(self, req, **_kwargs):
		graph = Te_controller.graph.translate_to_dict()
		LOG.debug("Graph returned: %s" % (graph))
		return Response(content_type='application/json', body=json.dumps(graph))


	def _process_hello(self, src_router_id, desig_router_id, nbors):
		LOG.info("**HELLO**: src_router_id:%s, designated_router:%s, nbors:%s" % (src_router_id, desig_router_id, nbors))
		graph = Te_controller.graph
		g = graph.getG()
		if len(nbors) == 0 or src_router_id not in g:
			return
		for nb in nbors:
			if nb not in g[src_router_id].ActiveNbs:
				g[src_router_id].ActiveNbs[nb] = 1
			if src_router_id not in g[nb].ActiveNbs:
				g[nb].ActiveNbs[src_router_id] = 1

		refresh_timer = time.time()-graph.neighbor_last_refresh 
		if refresh_timer > graph.NB_REFRESH_INTERVAL: #refresh the active neighbors graph periodically
			self._update_active_nbs_graph(g)
			graph.neighbor_last_refresh = time.time()
	                graph.print_me()
		
	#not used
	def _is_active_nbs_changed(self, router_id, new_nbs):
		g = Te_controller.graph.getG()
		router_nbs = g.getV(src_router_id).ActiveNbs
		if len(new_nbs) != len(router_nbs) or len(set(router_nbs) & set(new_nbs)) > 0:
			return 1
		return 0
	#not used
	def _update_active_nbs(self, router_id, new_nbs):
		g = Te_controller.graph.getG()
		router_nbs = g.getV(src_router_id).ActiveNbs
		for nb in router_nbs:
			if nb not in new_nbs:#delete adj
				Te_controller.graph.deleteAdj(router_id, nb)
		for nb in new_nbs:
			if nb not in router_nbs: #add adj
				Te_controller.graph.addAdj(router_id, nb)
		LOG.debug("Updated active nbs graph")
		
	def _update_active_nbs_graph(self, g):
		LOG.info("Updating active neighbors ...")
		LOG.debug(Te_controller.graph.printNB())
		for router_id in g:
			active_nbs = g[router_id].ActiveNbs
			router_nbs = {}
			for adj in g[router_id].IntraAdjs:
				router_nbs[adj.DstRouterID] = 1
				if adj.DstRouterID not in active_nbs: #delete the neighbor that is no longer active
					#Te_controller.graph.deleteAdj(router_id, adj.DstRouterID)
					Te_controller.graph.markDeletedAdj(router_id, adj.DstRouterID)
			for active_nb in active_nbs:
				if active_nb not in router_nbs: #add the active neighbor that is now active
					Te_controller.graph.addAdj(router_id, active_nb)
		return 0

	#Logic:
	#	- If router does not exist, create a new one.
	#	- If router existed, delete all existing adjs that aren't specified in the LSA.
	#	- Create adjs that don't exist and are specified in the LSA.
	def _process_rtr_lsa(self, lsa, lsid, advrtr):
		LOG.info("**Router LSA**: lsid:%s, advrtr:%s" % (lsid, advrtr))
		LOG.info("**Router LSA**: %s\n\n" % lsa)
		src_router_adjs = defaultdict(list)
		src_router_id = advrtr
		src_router = self._fetch_router(src_router_id)
		if src_router != None:
			pass
		else:
			src_router = V(ID=src_router_id, IntraAdjs = [], Prefixes = [], ActiveNbs = {})

		#construct adjs of the 2 endpoint routers
		#Note: if there is an ADJ from router 1 -> router 2, then there is automatically another ADJ from router 2 -> router 1.
		for intf in lsa['INTERFACES']:
			dst_router_id = intf['NBROUTERID']
			w = intf['METRIC']
			#adv router and neighbor router are the same, skip this LSA
			if src_router_id == dst_router_id:
				#src_router = None
				continue

			dst_router = self._fetch_router(dst_router_id)
			src_intf_id = intf['INTERFACEID']
			dst_intf_id = intf['NBINTERFACEID']
			#src_router_adjs[src_router_id].append(dst_router_id)
			src_router_adj = self._fetch_adj(src_router_id, dst_router_id, src_intf_id)
			dst_router_adj = self._fetch_adj(dst_router_id, src_router_id, dst_intf_id)
			if dst_router != None: #update
				pass 
			else:	#new
				dst_router = V(ID=dst_router_id, IntraAdjs = [], Prefixes = [], ActiveNbs = {})
			if src_router_adj: #update
				if 0 != self._update_adj(src_router_id, dst_router_id, src_intf_id, dst_intf_id, None, None, w):
					LOG.warn("Can't update adj (%s, %s)" % (src_router_id, dst_router_id))

			else:	#new
				src_router_adj = IntraAdj(LSID=src_intf_id, W=w, Prefixes=None, SrcRouterID=src_router_id, DstRouterID = dst_router_id, DstRouter=dst_router, SrcInterfaceID=src_intf_id, SrcInterfaceAddr=None, DstInterfaceID=dst_intf_id)
				src_router.IntraAdjs.append(src_router_adj)
			
			if dst_router_adj: #update
				if 0 != self._update_adj(dst_router_id, src_router_id, dst_intf_id, src_intf_id, None, None, w):
					LOG.warn("Can't update adj (%s, %s)" % (dst_router_id, src_router_id))
			else:	#new
				dst_router_adj = IntraAdj(LSID=dst_intf_id, W=w, Prefixes=None, SrcRouterID=dst_router_id, DstRouterID = advrtr, DstRouter=src_router, SrcInterfaceID=dst_intf_id, SrcInterfaceAddr=None, DstInterfaceID=src_intf_id)
				dst_router.IntraAdjs.append(dst_router_adj)

			#update the router in graph
			Te_controller.graph.addV(dst_router)
	
		#Delete adjs that are not specified in the LSA
		#if 0 != self._remove_adjs(src_router_id, src_router_adjs):
		#	LOG.warn("Can't remove adjacencies in router %s" % src_router_id)

		#update the router in graph
		Te_controller.graph.addV(src_router)
		Te_controller.graph.remove_duplicated_adjs(src_router_id)
		Te_controller.graph.print_me()
		

	def _process_link_lsa(self, lsa, lsid, advrtr):
		LOG.info("**Link LSA**: lsid:%s, advrtr:%s" % (lsid, advrtr))
		LOG.info("**Link LSA**: %s\n\n" % lsa)
		src_router_id = advrtr
		src_router = self._fetch_router(src_router_id)
		prefixes = lsa['prefixes']
		lladdr = lsa['linklocaladdress']
		if src_router:
			src_router.Prefixes = prefixes
		else:
			src_router = V(ID=src_router_id, IntraAdjs = [], Prefixes = prefixes, ActiveNbs = {})

		src_router_adj = self._fetch_adj(src_router_id, None, lsid)
		if src_router_adj:
			if 0 != self._update_adj(src_router_id, None,  lsid, None, prefixes, lladdr):
					LOG.warn("Can't update adj (router_id,lsid) = (%s, %s)" % (src_router_id, ls_id))

		else:
			src_router_adj = IntraAdj(LSID=lsid, W=0, Prefixes=prefixes, SrcRouterID=src_router_id, DstRouterID = None, DstRouter=None, SrcInterfaceID=lsid, SrcInterfaceAddr=lladdr, DstInterfaceID=None)
			src_router.IntraAdjs.append(src_router_adj)

		Te_controller.graph.addV(src_router)
		Te_controller.graph.print_me()
			
				
		

	def _process_network_lsa(self, lsa, lsid, advrtr):
		LOG.info("**Network LSA**: lsid:%s, advrtr:%s" % (lsid, advrtr))
		LOG.info("**Network LSA**: %s\n\n"% lsa)
		src_router_id = advrtr
		for rtr in lsa['RTRS']:
			if rtr == src_router_id:
				continue
			dst_router_id = rtr
			src_router = self._fetch_router(src_router_id)
			dst_router = self._fetch_router(dst_router_id)
			src_intf_id = lsid
			src_router_adj = self._fetch_adj(src_router_id, dst_router_id, src_intf_id)
			dst_router_adj = self._fetch_adj(dst_router_id, src_router_id)
			if src_router:
				pass
			else:
				src_router = V(ID=src_router_id, IntraAdjs = [], Prefixes = [], ActiveNbs = {})
			if dst_router:
				pass
			else:
				dst_router = V(ID=dst_router_id, IntraAdjs = [], Prefixes = [], ActiveNbs = {})

			if src_router_adj: #update adj
				if 0 != self._update_adj(src_router_id, dst_router_id, src_intf_id, None):
					LOG.warn("Can't update adj (%s, %s)" % (src_router_id, dst_router_id))
			else:	#new adj
				src_router_adj = IntraAdj(LSID=lsid, W=0, Prefixes=None, SrcRouterID=src_router_id, DstRouterID = dst_router_id, DstRouter=dst_router, SrcInterfaceID=None, SrcInterfaceAddr=None, DstInterfaceID=None)
				src_router.IntraAdjs.append(src_router_adj)
				
			if dst_router_adj: #update adj
				if 0 != self._update_adj(dst_router_id, src_router_id, None, src_intf_id, None):
					LOG.warn("Can't update adj (%s, %s)" % (dst_router_id, src_router_id))
			
			else:	#new adj
				dst_router_adj = IntraAdj(LSID=None, W=0, Prefixes=None, SrcRouterID=dst_router_id, DstRouterID=src_router_id, DstRouter=src_router, SrcInterfaceID=None, SrcInterfaceAddr=None, DstInterfaceID=None)
				dst_router.IntraAdjs.append(dst_router_adj)
		#update the nodes in graph
		Te_controller.graph.addV(dst_router)
		Te_controller.graph.addV(src_router)
		Te_controller.graph.remove_duplicated_adjs(src_router_id)
		Te_controller.graph.print_me()
	


	def _process_intraareaprefix_lsa(self, lsa, lsid, advrtr):
		reflsid = lsa['reflsid']
		src_router_id = lsa['refadvrouter']
		prefixes = lsa['prefixes']
		LOG.info("**Intra Area Prefix LSA**: lsid:%s, advrtr:%s, reflsid:%s, refadvrouterid:%s" % (lsid, advrtr, reflsid, src_router_id))
		LOG.info("**Intra Area Prefix LSA**: %s\n\n" % lsa)
		src_router = self._fetch_router(src_router_id)
		if src_router:
			src_router.Prefixes = prefixes
		else:
			src_router = V(ID=src_router_id, IntraAdjs = [], Prefixes = prefixes, ActiveNbs = {})

		src_router_adj = self._fetch_adj(src_router_id, None, reflsid)
		if src_router_adj:
			if 0 != self._update_adj(src_router_id, None,  reflsid, None, prefixes, None, None):
					LOG.warn("Can't update adj (router_id,lsid) = (%s, %s)" % (src_router_id, reflsid))

		else:
			src_router_adj = IntraAdj(LSID=reflsid, W=0, Prefixes=prefixes, SrcRouterID=src_router_id, DstRouterID = None, DstRouter=None, SrcInterfaceID=reflsid, SrcInterfaceAddr=None, DstInterfaceID=None)
			src_router.IntraAdjs.append(src_router_adj)

		Te_controller.graph.addV(src_router)
		Te_controller.graph.print_me()


	def _remember_adjs(self, router_adjs, src_router_id, dst_router_id):
		if src_router_id in router_adjs:
			router_adjs[src_router_id].append(dst_router_id)
		else:
			router_adjs[src_router_id] = [dst_router_id]
		return 0

	def _remove_adjs(self, router_id, router_adjs):
		if router_id not in router_adjs:
			return 0
		g = Te_controller.graph.getG()	
		if router_id not in g:
			return -1
		for adj in g[router_id].IntraAdjs:
			LOG.debug("Removing adj: router:%s, dst_router:%s, router_adjs:%s" % (router_id, adj.DstRouterID, router_adjs))
			if adj.DstRouterID != None and not adj.DstRouterID in router_adjs[router_id]:
				Te_controller.graph.deleteAdj(router_id, adj.DstRouterID)
				if adj.DstRouterID != None:
					Te_controller.graph.deleteAdj(adj.DstRouterID, router_id) #also delete the oposite adj
					LOG.debug("Removed adj: router:%s, dst_router:%s, router_adjs:%s" % (adj.DstRouterID, router_id, router_adjs))
				LOG.debug("Removed adj: router:%s, dst_router:%s, router_adjs:%s" % (router_id, adj.DstRouterID, router_adjs))
		return 0

	#not used
	def _is_adj_exist(self, src_router_id, dst_router_id):
		g = Te_controller.graph.getG()
		if src_router_id not in g:
			return False

		for adj in g[routerID].IntraAdjs:
			if dst_router_id == adj.DstRouterID:
				return True
		return False

	def _fetch_router(self, router_id):
		g = Te_controller.graph.getG()
		if router_id in g:
			return g[router_id]
		return None

	def _fetch_adj_by_router_ids(self, src_router_id, dst_router_id, g):
		LOG.debug("_fetch_adj_by_router_ids %s, %s" % (src_router_id, dst_router_id))
		if src_router_id not in g:
			return None
		for adj in g[src_router_id].IntraAdjs:
			if dst_router_id == adj.DstRouterID:
				if adj.D == 1:
					adj.D = 0	#make this adj alive again!
				return adj
		return None

	def _fetch_adj_by_lsid(self, router_id, lsid, g):
		LOG.debug("_fetch_adj_by_lsid %s, %s" % (router_id, lsid))
		if router_id not in g:
			return None
		for adj in g[router_id].IntraAdjs:
			if lsid == adj.LSID:
				if adj.D == 1:
					adj.D = 0	#make this adj alive again!
				return adj
		return None

	def _fetch_adj(self, src_router_id = None, dst_router_id = None, lsid = None):
		ret = None
		g = Te_controller.graph.getG()
		if src_router_id != None and dst_router_id != None:
			 ret = self._fetch_adj_by_router_ids(src_router_id, dst_router_id, g)
		if ret == None and src_router_id != None and lsid != None:
			 ret = self._fetch_adj_by_lsid(src_router_id, lsid, g)
		return ret



	def _update_adj(self, src_router_id, dst_router_id, src_intf_id=None, dst_intf_id=None, src_router_prefixes=None, src_router_lladdr=None, W=None):
		LOG.debug("update adj: src_router_id:%s, dst_router_id:%s, src_intf_id:%s, dst_intf_id:%s, src_router_prefixes:%s, src_router_lladdr:%s, w:%s" % (src_router_id, dst_router_id, src_intf_id, dst_intf_id, src_router_prefixes, src_router_lladdr, W))
		g = Te_controller.graph.getG()
		r1 = 0
		r2 = 0
		if src_router_id != None and dst_router_id != None:
			new_adj = self._fetch_adj_by_router_ids(src_router_id, dst_router_id, g)
			r1 = self._update_adj_by_router_ids(src_router_id, dst_router_id, new_adj, src_intf_id, dst_intf_id, src_router_prefixes, src_router_lladdr, W, g)
		if src_router_id != None and src_intf_id != None:
			new_adj = self._fetch_adj_by_lsid(src_router_id, src_intf_id, g)
			r2 = self._update_adj_by_lsid(src_router_id, new_adj, dst_router_id, src_intf_id, dst_intf_id, src_router_prefixes, src_router_lladdr, W, g)
		return max(r1, r2)

	def _update_adj_by_lsid(self, src_router_id, new_adj, dst_router_id = None, src_intf_id = None, dst_intf_id = None, src_router_prefixes = None, src_router_lladdr = None, W=None, g = None):
		if not g:
			LOG.warn("The topology graph is empty!")
			return -1
		lsid = src_intf_id
		if src_router_id not in g:
			LOG.warn("Can't find router %s" % src_router_id)
			return -1
		for i in range(0, len(g[src_router_id].IntraAdjs)):
			if lsid == g[src_router_id].IntraAdjs[i].LSID:
				
				new_adj._update(src_router_id, dst_router_id, src_intf_id, dst_intf_id, src_router_prefixes, src_router_lladdr, W)
				g[src_router_id].IntraAdjs[i] = new_adj 
				LOG.debug("Updated: _update_adj_by_lsid")
		return 0

	def _update_adj_by_router_ids(self, src_router_id, dst_router_id, new_adj, src_intf_id=None, dst_intf_id=None, src_router_prefixes = None, src_router_lladdr = None, W=None, g = None):
		if not g:
			LOG.warn("The topology graph is empty!")
			return -1
		if src_router_id not in g:
			LOG.warn("Can't find router %s" % src_router_id)
			return -1
		for i in range(0, len(g[src_router_id].IntraAdjs)):
			if dst_router_id == g[src_router_id].IntraAdjs[i].DstRouterID:
				new_adj._update(src_router_id, dst_router_id, src_intf_id, dst_intf_id, src_router_prefixes, src_router_lladdr, W)
				g[src_router_id].IntraAdjs[i] = new_adj 
				LOG.debug("Updated: _update_adj_by_router_ids")
		return 0





			
