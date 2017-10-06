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

class IntraAdj(object):
	def __init__(self, **kwargs):
		self.LSID = kwargs['LSID']
		self.W = kwargs['W']
		self.Prefix = kwargs['Prefix']
		self.DstRouterID = kwargs['DstRouterID']
		self.DstRouter = kwargs['DstRouter']
		self.SrcInterface = kwargs['SrcInterface']
		self.DstInterface = kwargs['DstInterface']

	def print_me(self):
		LOG.info("LS:\n"
			"\t	LSID:%s\n" 
			"\t	DstRouterID:%s\n" 
			"\t	DstRouter:%s\n "
			"\t	Src/Dst Interfaces:%s, %s\n" 
			"\t	W:%s\n"
			"\t	Prefix:%s\n" % (self.LSID, self.DstRouterID, self.DstRouter, self.SrcInterface, self.DstInterface, self.W, self.Prefix) 
		)

'''
class LS(object):
	def __init__(self, **kwargs):
		self.LSID = kwargs['LSID']
		self.AtcRouterIDs = kwargs['AtcRouterIDs']
		self.AtcRouters = kwargs['AtcRouters']
		self.AtcInterfaces = kwargs['AtcInterfaces']
		self.W = kwargs['W']
		self.Prefix = kwargs['Prefix']
 
	def print(self):
		LOG.info("LS:\n
			\t	LSID:%s\n  
			\t	AtcRouterIDs:%s, %s\n 
			\t	AtcRouters:%s, %s\n 
			\t	AtcInterfaces:%s, %s\n 
			\t	W:%s\n
			\t	Prefix:%s\n" % (self.LSID, self.AtcRouterIDs[0], self.AtcRouterIDs[1], self.AtcRouters[0], self.AtcRouters[1], self.AtcInterfaces[0], self.AtcInterfaces[1], self.W, self.Prefix) 
		)
'''
class G(object):
	def __init__(self, **kwargs):
		self.G = {}
	def addV(self, V):
		self.G[V.ID] = V
	def getV(self, ID):
		return self.G[ID]
	def delV(self, ID):
		del self.G[ID]
	def print_me(self):
		for ID in self.G:
			LOG.info("VID=%s, V=%s\n" % (ID, self.G[ID]))
