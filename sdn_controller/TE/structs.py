#!/usr/bin/python2.7
import logging as LOG
import time, sys, re
from collections import defaultdict

MSG_TYPES = { 1L: "HELLO",
              2L: "DBDESC",
              3L: "LSREQ",
              4L: "LSUPD",
              5L: "LSACK",
              }
ADJ_DICT = {
		'LSID': 1,
		'W': 1,
		'Prefixes' : 1,
		'SrcRouterID' : 1,
		'DstRouterID' : 1,
		'SrcInterfaceID': 1,
		'SrcInterfaceAddr': 1,
		'DstInterfaceID': 1
	}

NODE_DICT = {
		'ID': 1,
		'IntraAdjs': 1,
		'Prefixes' : 1,
		'ActiveNbs' : 1
	}


class V(object):
	def __init__(self, **kwargs):
		self.ID = kwargs['ID']
		self.IntraAdjs = kwargs['IntraAdjs']
		self.Prefixes = kwargs['Prefixes']
		self.ActiveNbs = kwargs['ActiveNbs']

class IntraAdj(object):
	def __init__(self, **kwargs):
		self.LSID = kwargs['LSID']
		self.W = kwargs['W']
		self.Prefixes = kwargs['Prefixes']
		self.SrcRouterID = kwargs['SrcRouterID']
		self.DstRouterID = kwargs['DstRouterID']
		self.DstRouter = kwargs['DstRouter']
		self.SrcInterfaceID = kwargs['SrcInterfaceID']
		self.SrcInterfaceAddr = kwargs['SrcInterfaceAddr']
		self.DstInterfaceID = kwargs['DstInterfaceID']
		self.D = 0	#mark 1 if the adj is deleted
		#self.DstInterfaceAddr = kwargs['DstInterfaceAddr']

	def _update(self, src_router_id = None, dst_router_id = None, src_intf_id = None, dst_intf_id = None, src_router_prefixes = None, src_router_lladdr = None, W = None):
		if src_intf_id != None:
	        	self.LSID = src_intf_id
		if src_router_id != None:
			self.SrcRouterID = src_router_id 
		if W != None:
			self.W = W 
		if dst_router_id != None:
			self.DstRouterID = dst_router_id
		if src_intf_id != None:
			self.SrcInterfaceID = src_intf_id
		if dst_intf_id != None:
			self.DstInterfaceID = dst_intf_id
		self._update_prefixes(src_router_prefixes)
		if src_router_lladdr != None:
			self.SrcInterfaceAddr = src_router_lladdr

	def _update_prefixes(self, new_prefixes):
		if new_prefixes:
			if self.Prefixes:
				for p in new_prefixes:
					if p not in self.Prefixes:
						self.Prefixes.append(p)
			else:
				self.Prefixes = new_prefixes
			
	def print_me(self):
		LOG.info("LS:\n"
			"\t	Mark deleted:%s\n" \
			"\t	LSID:%s\n" 
			"\t	SrcRouterID:%s\n" 
			"\t	DstRouterID:%s\n" 
			"\t	DstRouter:%s\n "
			"\t	Src/Dst Interface IDs:%s, %s\n" 
			"\t	Src Interface Address:%s\n" 
			"\t	W:%s\n"
			"\t	Prefixes:%s\n" % (self.D, self.LSID, self.SrcRouterID, self.DstRouterID, self.DstRouter, self.SrcInterfaceID, self.DstInterfaceID, self.SrcInterfaceAddr, self.W, self.Prefixes) 
		)
	def str_me(self):
		return "LS:\n"\
			"\t	Mark deleted:%s\n" \
			"\t	LSID:%s\n" \
			"\t	SrcRouterID:%s\n" \
			"\t	DstRouterID:%s\n" \
			"\t	DstRouter:%s\n "\
			"\t	Src/Dst Interface IDs:%s, %s\n" \
			"\t	Src Interface Address:%s\n" \
			"\t	W:%s\n"\
			"\t	Prefixes:%s\n" % (self.D, self.LSID, self.SrcRouterID, self.DstRouterID, self.DstRouter, self.SrcInterfaceID, self.DstInterfaceID, self.SrcInterfaceAddr, self.W, self.Prefixes) 


class G(object):
	NB_REFRESH_INTERVAL = 10 #in seconds 
	def __init__(self, **kwargs):
		self.G = {}
		self.neighbor_last_refresh = sys.maxint
	def getG(self):
		return self.G
	def addV(self, V):
		if V:
			self.G[V.ID] = V
	def getV(self, ID):
		if ID in self.G:
			return self.G[ID]
		return None
	def delV(self, ID):
		del self.G[ID]
	def markDeletedAdj(self, src_router_id, dst_router_id):
		index = 0
		for adj in self.G[src_router_id].IntraAdjs:
			if adj.LSID != 0 and adj.DstRouterID == dst_router_id:	#a bit conservative here.
				self.G[src_router_id].IntraAdjs[index].D = 1
			index += 1
		if self.G[src_router_id].IntraAdjs == None:
			self.G[src_router_id].IntraAdjs = []

	def deleteAdj(self, src_router_id, dst_router_id):
		index = 0
		for adj in self.G[src_router_id].IntraAdjs:
			if adj.LSID != 0 and adj.DstRouterID == dst_router_id:
				del self.G[src_router_id].IntraAdjs[index]
			index += 1
		if self.G[src_router_id].IntraAdjs == None:
			self.G[src_router_id].IntraAdjs = []

	def addAdj(self, src_router_id, dst_router_id):
		if src_router_id not in self.G:
			return 1
		src_router = self.G[src_router_id]
		dst_router = V(ID=dst_router_id, IntraAdjs = [], Prefixes = [], ActiveNbs = {})
		#src->dst
		src_router_adj = IntraAdj(LSID=None, W=None, Prefixes=None, SrcRouterID=src_router_id, DstRouterID = dst_router_id, DstRouter=dst_router, SrcInterfaceID=None, SrcInterfaceAddr=None, DstInterfaceID=None)
		src_router.IntraAdjs.append(src_router_adj)
		#dst->src
		dst_router_adj = IntraAdj(LSID=None, W=None, Prefixes=None, SrcRouterID=dst_router_id, DstRouterID = src_router_id, DstRouter=src_router, SrcInterfaceID=None, SrcInterfaceAddr=None, DstInterfaceID=None)
		dst_router.IntraAdjs.append(dst_router_adj)
		return 0

	def remove_duplicated_adjs(self, router_id):
		LOG.debug("remove_duplicated_adjs, router_id:%s" % router_id)
		adjs = {}
		index = 0
		for adj in self.G[router_id].IntraAdjs:
			lsid = adj.LSID
			dst_router_id = adj.DstRouterID
			if dst_router_id in adjs and lsid == adjs[dst_router_id]:
				del self.G[router_id].IntraAdjs[index]
			else:
				adjs[dst_router_id] = lsid
			index += 1
		self.print_me()

	def print_me(self):
		for ID in self.G:
			LOG.info("RouterID:%s\n" % (ID))
			for adj in self.G[ID].IntraAdjs:
				if adj.D == 0:
					LOG.info("\tsrcRtrID:%s,LSID:%s,W:%s,Prefixes:%s,srcIntfID:%s,srcIntfAddr:%s,dstIntfID:%s,dstRtrId:%s\n" % (adj.SrcRouterID, adj.LSID, adj.W, adj.Prefixes, adj.SrcInterfaceID, adj.SrcInterfaceAddr, adj.DstInterfaceID, adj.DstRouterID))

	def printNB(self):
		ret = ""
		for ID in self.G:
			ret += "RouterID:%s, Active NBs:%s\n" % (ID, self.G[ID].ActiveNbs)
		return ret

	def clear_active_nbs(self):
		for ID in self.G:
			self.G[ID].ActiveNbs = {}

	def translate_to_dict(self):
		G_dict = {}
		for ID in self.G:
			V_dict = {}
			for f in NODE_DICT:
				if f == 'IntraAdjs':
					adj_dict = {}
					for adj in self.G[ID].IntraAdjs:
						for f1 in ADJ_DICT:
							adj_dict[f1] = getattr(adj, f1)
					V_dict['IntraAdjs'] = adj_dict
				else:
					V_dict[f] = getattr(self.G[ID], f)
			G_dict[ID] = V_dict
		return G_dict

	def translate_to_dict_netjson(self):
		netjson = {
		    "type": "NetworkGraph",
		    "label": "Traffic Engineer Topology Graph",
		    "protocol": "OSPFv3",
		    "version": "0.0.0.1",
		    "metric": "Bandwidth",
		}
		nodes = []
		links = []
		for ID in self.G:
			#node
			n = self.G[ID]
			
			properties = {
				"Node segment": self._get_node_segments(n),
				"Prefixes" : self._get_prefixes(n),
			}
			node = {
				"id": ID,
				"lable": "Router %s" % ID,
				"properties":properties
			}
			nodes.append(node)
			#adjacencies
			found_adjs = {}
			for adj in self.G[ID].IntraAdjs:
				if adj.LSID == 0 or adj.D == 1:
					continue
				[src_adj_segment, dst_adj_segment] = self._get_adj_segments(self.G, adj)
				link_properties = {
					"Linkstate ID": adj.LSID,
					"Prefixes": adj.Prefixes,
					"Src Interface Address": src_adj_segment,
					"Dst Interface Address": dst_adj_segment,
					"OSPF cost (bandwidth)": "%s Mbps" % adj.W,
				}
				edge = {
					"source": adj.SrcRouterID,
					"target": adj.DstRouterID, 
					"cost": adj.W,
					"properties": link_properties
				}
				links.append(edge)
		netjson["nodes"] = nodes
		netjson["links"] = links
		return netjson

	def _get_prefixes(self, node):
		for adj in node.IntraAdjs:
			if adj.LSID == 0:
				return adj.Prefixes
		return None


	def _get_node_segments(self, node):
		segs = []
		for adj in node.IntraAdjs:
			if adj.LSID == 0:
				for p in adj.Prefixes:
					if re.match(r'.*::1', p) != None:
						segs.append(p)
		return segs

	def _get_adj_segments(self, graph, adj):
		src_adj_segment = self._generate_adj_segment(adj.SrcInterfaceAddr, adj.Prefixes)
		reversed_adj = None
		dst_adj_segment = None
		for r_adj in graph[adj.DstRouterID].IntraAdjs:
			if r_adj.DstRouterID == adj.SrcRouterID:
				reversed_adj = r_adj
		if reversed_adj != None:
			dst_adj_segment = self._generate_adj_segment(reversed_adj.SrcInterfaceAddr, reversed_adj.Prefixes)
		return [src_adj_segment, dst_adj_segment]
			

	#Generate a SR adjacency segment using link-local address and prefix.
	#This is a bit cheating because for this to work the adj segment
	#(or router interface's address) must be *assigned* such that 
	#its 2nd portion is exactly the same as the 2nd portion of the link-local 
	#address. To make it clean, OSPF must be extended to advertise 
	#adjacency segment addresses. 
	def _generate_adj_segment(self, ll_addr, prefixes):
		if len(prefixes) == 0:
			return None
		longest_prefix = prefixes[0]
		for p in prefixes:
			if len(p) > len(longest_prefix):
				longest_prefix = p
		second_portion = ":".join(ll_addr.split(":")[3:])
		first_portion = longest_prefix[:-1]
		LOG.debug("_generate_adj_segment: 1st protion:%s, 2nd portion:%s" % (first_portion, second_portion))
		return "%s%s" % (first_portion, second_portion)
