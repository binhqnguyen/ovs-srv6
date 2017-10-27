#!/usr/bin/python2.7
import logging as LOG

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
		self.DstInterfaceAddr = kwargs['DstInterfaceAddr']

	def _update(self, src_router_id = None, dst_router_id = None, src_intf_id = None, dst_intf_id = None, src_router_prefixes = None, src_router_lladdr = None):
	        self.LSID = src_intf_id if src_intf_id else self.LSID
		self.SrcRouterID = src_router_id if src_router_id else self.SrcRouterId
		self.DstRouterID = dst_router_id if dst_router_id else self.DstRouterId
		self.SrcInterfaceID = src_intf_id if src_intf_id else self.SrcInterfaceID
		self.DstInterfaceID = dst_intf_id if dst_intf_id else self.DstInterfaceID
		self.Prefixes = src_router_prefixes if src_router_prefixes else self.Prefixes
		self.SrcInterfaceAddr = src_router_lladdr if src_router_lladdr else self.SrcInterfaceAddr

	def print_me(self):
		LOG.info("LS:\n"
			"\t	LSID:%s\n" 
			"\t	SrcRouterID:%s\n" 
			"\t	DstRouterID:%s\n" 
			"\t	DstRouter:%s\n "
			"\t	Src/Dst Interface IDs:%s, %s\n" 
			"\t	Src/Dst Interfaces Addresses:%s, %s\n" 
			"\t	W:%s\n"
			"\t	Prefixes:%s\n" % (self.LSID, self.SrcRouterID, self.DstRouterID, self.DstRouter, self.SrcInterfaceID, self.DstInterfaceID, self.SrcInterfaceAddr, self.DstInterfaceAddr, self.W, self.Prefixes) 
		)
	def str_me(self):
		return "LS:\n"\
			"\t	LSID:%s\n" \
			"\t	SrcRouterID:%s\n" \
			"\t	DstRouterID:%s\n" \
			"\t	DstRouter:%s\n "\
			"\t	Src/Dst Interface IDs:%s, %s\n" \
			"\t	Src/Dst Interfaces Addresses:%s, %s\n" \
			"\t	W:%s\n"\
			"\t	Prefixes:%s\n" % (self.LSID, self.SrcRouterID, self.DstRouterID, self.DstRouter, self.SrcInterfaceID, self.DstInterfaceID, self.SrcInterfaceAddr, self.DstInterfaceAddr, self.W, self.Prefixes) 


class G(object):
	def __init__(self, **kwargs):
		self.G = {}
	def getG(self):
		return self.G
	def addV(self, V):
		if V:
			self.G[V.ID] = V
	def getV(self, ID):
		return self.G[ID]
	def delV(self, ID):
		del self.G[ID]
	def print_me(self):
		for ID in self.G:
			LOG.info("RouterID:%s\n" % (ID))
			for adj in self.G[ID].IntraAdjs:
				LOG.info("\tsrcRtrID:%s,LSID:%s,Prefixes:%s,srcIntfID:%s,srcIntfAddr:%s,dstIntfID:%s,dstIntfAddr:%s,dstRtrId:%s\n" % (adj.SrcRouterID, adj.LSID,  adj.Prefixes, adj.SrcInterfaceID, adj.SrcInterfaceAddr, adj.DstInterfaceID, adj.DstInterfaceAddr, adj.DstRouterID))
