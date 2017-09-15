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


