#!/usr/bin/python2.7
import logging as LOG
import time, sys

MSG_TYPES = { 1L: "HELLO",
              2L: "DBDESC",
              3L: "LSREQ",
              4L: "LSUPD",
              5L: "LSACK",
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
	NB_REFRESH_INTERVAL = 60 #in seconds 
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
	def markDeleteAdj(self, src_router_id, dst_router_id):
		index = 0
		for adj in self.G[src_router_id].IntraAdjs:
			if adj.LSID != None and adj.LSID != 0 and adj.DstRouterID == dst_router_id:	#a bit conservative here.
				#del self.G[src_router_id].IntraAdjs[index]
				self.G[src_router_id].IntraAdjs[index].D = 1
			index += 1
		if self.G[src_router_id].IntraAdjs == None:
			self.G[src_router_id].IntraAdjs = []

	def deleteAdj(self, src_router_id, dst_router_id):
		index = 0
		for adj in self.G[src_router_id].IntraAdjs:
			if adj.LSID != None and adj.LSID != 0 and adj.DstRouterID == dst_router_id:	#a bit conservative here.
				del self.G[src_router_id].IntraAdjs[index]
			index += 1
		if self.G[src_router_id].IntraAdjs == None:
			self.G[src_router_id].IntraAdjs = []

	def addAdj(self, src_router_id, dst_router_id):
		if src_router_id not in G:
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
			self.G[ID].ActiveNBs = {}

