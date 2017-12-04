#define pr_fmt(fmt) KBUILD_MODNAME ": " fmt

#include <linux/version.h>
#include <linux/in.h>
#include <linux/ip.h>
#include <linux/net.h>
#include <linux/rculist.h>
#include <linux/udp.h>

#include <net/icmp.h>
#include <net/ip.h>
#include <net/route.h>
#include <net/udp.h>
#include <net/xfrm.h>

#include "datapath.h"
#include "vport.h"
#include <linux/icmp.h>

#include <linux/if_arp.h>




//struct gtphdr{
//	// need to make bit struct fields for flags
//	__be16 gtp_flags;
//	__be16 gtp_total_len;
//	__be32 gtp_teid;
//};



/**
 * struct srv6_port - Keeps track of open UDP ports
 * @dst_port: srv6 port no.
 * @list: list element in @srv6_ports.
 * @srv6_rcv_socket: The socket created for this port number.
 * @name: vport name.
 */
struct srv6_port {
	__be16 dst_port;
	struct list_head list;
	struct socket *srv6_rcv_socket;
	char name[IFNAMSIZ];
};

static LIST_HEAD(srv6_ports);

static inline struct srv6_port *get_srv6_port(const struct vport *vport)
{
	return vport_priv(vport);
}

static struct srv6_port *srv6_find_port(struct net *net, __be16 port)
{
	struct srv6_port *srv6_port;

	list_for_each_entry_rcu(srv6_port, &srv6_ports, list) {
		if (srv6_port->dst_port == port &&
			net_eq(sock_net(srv6_port->srv6_rcv_socket->sk), net))
			return srv6_port;
	}

	return NULL;
}

//BN: testing
const struct in6_addr tun_src =
        { { .u6_addr32 = { 0x00000120, 0x00000000, 0xff234020, 0xfe40b7fe } } };
#ifdef _SR_
#define OVS_CB_SIZE 48
#define OFFSET_MAC 14
#endif

static void set_mac_addr(unsigned char* dst, unsigned char* src, int size)
{
	memcpy(dst, src, size);
}

unsigned short hex_to_decimal_for_port(unsigned char* port)
{
        unsigned short srv6_port = 0;
        srv6_port |= port[0] << 8;
        srv6_port |= port[1];
        return srv6_port;
}

/* Compute checksum for count bytes starting at addr, using one's complement of one's complement sum*/
static unsigned short compute_checksum(unsigned short *addr, unsigned int count) 
{
  register unsigned long sum = 0;
  while (count > 1) {
    sum += * addr++;
    count -= 2;
  }
  //if any bytes left, pad the bytes and add
  if(count > 0) {
    sum += ((*addr)&htons(0xFF00));
  }
  //Fold sum to 16 bits: add carrier to result
  while (sum>>16) {
      sum = (sum & 0xffff) + (sum >> 16);
  }
  //one's complement
  sum = ~sum;
  return ((unsigned short)sum);
}


/* set ip checksum of a given ip header*/
void compute_ip_checksum(struct iphdr* iphdrp){
  iphdrp->check = 0;
  iphdrp->check = compute_checksum((unsigned short*)iphdrp, iphdrp->ihl<<2);
}


/* Called with rcu_read_lock and BH disabled. */
static int srv6_rcv(struct sock *sk, struct sk_buff *skb)
{
	return 0;
}

/* Arbitrary value.  Irrelevant as long as it's not 0 since we set the handler. */
#define UDP_ENCAP_GTP 65535
static int srv6_socket_init(struct srv6_port *srv6_port, struct net *net)
{
	struct sockaddr_in sin;
	int err;

	err = sock_create_kern(AF_INET, SOCK_DGRAM, 0,
			       &srv6_port->srv6_rcv_socket);
	if (err)
		goto error;

	/* release net ref. */
	sk_change_net(srv6_port->srv6_rcv_socket->sk, net);

	sin.sin_family = AF_INET;
	sin.sin_addr.s_addr = htonl(INADDR_ANY);
	sin.sin_port = srv6_port->dst_port;

	err = kernel_bind(srv6_port->srv6_rcv_socket, (struct sockaddr *)&sin,
			  sizeof(struct sockaddr_in));
	if (err)
		goto error_sock;

	udp_sk(srv6_port->srv6_rcv_socket->sk)->encap_type = UDP_ENCAP_GTP;
	udp_sk(srv6_port->srv6_rcv_socket->sk)->encap_rcv = srv6_rcv;

	udp_encap_enable();

	return 0;

error_sock:
	sk_release_kernel(srv6_port->srv6_rcv_socket->sk);
error:
	pr_warn("cannot register srv6 protocol handler: %d\n", err);
	return err;
}

static int srv6_get_options(const struct vport *vport, struct sk_buff *skb)
{
	struct srv6_port *srv6_port = get_srv6_port(vport);

	if (nla_put_u16(skb, OVS_TUNNEL_ATTR_DST_PORT, ntohs(srv6_port->dst_port)))
		return -EMSGSIZE;
	return 0;
}

static void srv6_tnl_destroy(struct vport *vport)
{
	struct srv6_port *srv6_port = get_srv6_port(vport);
	pr_warn("srv6 port destroy (vport-srv6.c)\n");

	list_del_rcu(&srv6_port->list);
	/* Release socket */
	sk_release_kernel(srv6_port->srv6_rcv_socket->sk);

	ovs_vport_deferred_free(vport);
}

static struct vport *srv6_tnl_create(const struct vport_parms *parms)
{
	struct net *net = ovs_dp_get_net(parms->dp);
	struct nlattr *options = parms->options;
	struct srv6_port *srv6_port;
	struct vport *vport;
	struct nlattr *a;
	int err;
	u16 dst_port;

	pr_warn("srv6 port create\n");
	if (!options) {
		err = -EINVAL;
		goto error;
	}

	a = nla_find_nested(options, OVS_TUNNEL_ATTR_DST_PORT);
	if (a && nla_len(a) == sizeof(u16)) {
		dst_port = nla_get_u16(a);
	} else {
		/* Require destination port from userspace. */
		err = -EINVAL;
		goto error;
	}

	/* Verify if we already have a socket created for this port */
	if (srv6_find_port(net, htons(dst_port))) {
		err = -EEXIST;
		goto error;
	}

	vport = ovs_vport_alloc(sizeof(struct srv6_port),
				&ovs_srv6_vport_ops, parms);
	if (IS_ERR(vport))
		return vport;

	srv6_port = get_srv6_port(vport);
	srv6_port->dst_port = htons(dst_port);
	strncpy(srv6_port->name, parms->name, IFNAMSIZ);

	err = srv6_socket_init(srv6_port, net);
	if (err)
		goto error_free;

	list_add_tail_rcu(&srv6_port->list, &srv6_ports);
	pr_warn("succeed creating srv6 port, port = %d\n", vport->port_no);
	return vport;

error_free:
	ovs_vport_free(vport);
error:
	return ERR_PTR(err);
}

void set_ehter_addr(struct ethhdr* ethh, char* src, char* dst)
{
	set_mac_addr(ethh->h_dest, dst, sizeof(ethh->h_dest));
	set_mac_addr(ethh->h_source, src, sizeof(ethh->h_source));
}


//static struct gtphdr* get_gtp_hdr(struct sk_buff* skb){
//	/* off_server & alice info + payload */
//	unsigned char* begin = skb->data;
//	int gtp_offset =  OFFSET_MAC + OFFSET_OUTER_IP + OFFSET_UDP;
//	return (struct gtphdr*)(begin+gtp_offset);
//}

//static struct iphdr* get_inner_iph_with_gtp(struct gtphdr* gtp_hdr)
//{
//	/* off_server & alice info + payload */
//	struct iphdr* inner_iph = (struct iphdr*)(gtp_hdr+1);
//	return inner_iph;
//
//}

//static struct iphdr* get_inner_iph(struct sk_buff* skb)
//{
//	/* off_server & alice info + payload */
//	unsigned char* begin = skb->data;
//	int outer_packet_len =  OFFSET_MAC + OFFSET_OUTER_IP + OFFSET_UDP + OFFSET_GTP;
//	struct iphdr* inner_iph = (struct iphdr*)(begin+outer_packet_len);
//
//	return inner_iph;
//
//}

//static void decap_srv6_packet_to_pure(struct sk_buff* skb)
//{
//	/* off_server & alice info + payload */
//	int outer_packet_len =  OFFSET_OUTER_IP + OFFSET_UDP + OFFSET_GTP;
//	unsigned char* outer_packet_point = skb->data + OFFSET_MAC;
//	unsigned char* inner_packet_point = outer_packet_point + outer_packet_len;
//	int inner_packet_len = skb->len - outer_packet_len - OFFSET_MAC;
//
//	/* remove outer_ip + udp + gtp */
//	memset(outer_packet_point, 0, outer_packet_len);
//	/* copy inner_ip to outer_ip place */
//	memcpy(outer_packet_point, inner_packet_point, inner_packet_len);
//	/* reset inner_packet area */
//	memset(outer_packet_point+inner_packet_len, 0, outer_packet_len);
//	skb->len = skb->len - outer_packet_len;
//
//	skb_set_network_header(skb,OFFSET_MAC);
//	skb_set_transport_header(skb, OFFSET_MAC+OFFSET_OUTER_IP);
//}

#ifdef _SR_
static void encap_pure_packet_to_srv6_segments(struct sk_buff* skb, struct ipv6_segments *segments)
{
        struct ethhdr* eth_hdr;
        struct ipv6hdr* outer_iph;
        struct rt2_hdr* srh;
        struct ipv6hdr* inner_iph;
        //struct ovs_key_ipv6_tunnel* tunnel;
        unsigned char* start_skb;
        uint8_t offset = 0;
	uint8_t i = 0;
	//uint8_t index = 0;

	if (segments){
		pr_warn("encap_pure_packet_to_srv6_segments: number of segment = %d\n", segments->segment_used);
		for (i = 0; i < segments->segment_used; i++){
			pr_warn("Segment %d: %02x\n", i, segments->ipv6_segments[i].addr[3]);
		}
	}

	offset = 40 + 8 + 16; //Outer IPV6 SR header = outer IPV6 header (40B) + SRH (8B) + 1 IPV6 segment (16B).
        eth_hdr = (struct ethhdr*)skb->data;


        start_skb = (unsigned char*)skb->data;
        memcpy(start_skb-offset, start_skb, sizeof(*eth_hdr)); //BN: copy ethernet header over, and leave space for GTP
        memset(start_skb, 0, sizeof(*eth_hdr)); //BN:clear the copied ethernet header in skb.

        skb_push(skb, offset);  //BN: Add data to the start of the buffer, create room for the IPV6 SRH
        skb_set_mac_header(skb, 0); //BN: set the MAC address pointer to begining of the extended skb->data.

        // To get information of the inner IPV6 header
        inner_iph = (struct ipv6hdr*)(eth_hdr+1); //BN: after the ethernet hdr is the inner IP header.

        //BN: to create an IPV6 header with SR header
        eth_hdr = (struct ethhdr*)(start_skb-offset);   // key point
        outer_iph = (struct ipv6hdr*) (eth_hdr+1);
        outer_iph->version      = 6;
        memcpy(outer_iph->flow_lbl,inner_iph->flow_lbl,3);
        outer_iph->payload_len  = __cpu_to_be16(offset + 40 + __be16_to_cpu(inner_iph->payload_len));  //BN:lenght of this IP packet (including the inner IP packet and inner IPv6 header (40B))
        outer_iph->nexthdr      = 43; //BN: IPV6 routing.
        outer_iph->hop_limit = inner_iph->hop_limit - 1;
        //BN: test only
        outer_iph->daddr        = tun_src;
        outer_iph->saddr        = tun_src;
	//BN: SR
        srh = (struct rt2_hdr*) (outer_iph+1);
	srh->rt_hdr.nexthdr = 41; //IPV6
	srh->rt_hdr.hdrlen = 0x02; //8 + 1 segment (16B) = 24
	srh->rt_hdr.type = 4;
	srh->rt_hdr.segments_left = 0;
	srh->reserved = 0x00000000;	//4B before segment
	srh->addr = tun_src;
        //compute_ip_checksum(outer_iph);       //BN: NO CHECHSUM REQUIRED. TODO, calculate checksum for IPV6 header.
        skb_set_network_header(skb,OFFSET_MAC); //BN:set the IP header pointer, ethernet offset = 14B
}

static int ovs_tnl_send_segments(struct vport *vport, struct sk_buff *skb, struct ipv6_segments *segments)
{
	int err = 0;
	struct srv6_port *srv6_port = get_srv6_port(vport);
	pr_warn("gtp ovs tnl send vport name = %s num = %u mac_len = %d, skb len = %d (vport-gtp.c)\n", 
	srv6_port->name, vport->port_no, skb->mac_len, skb->len);

	if (segments)
                pr_warn("ovs_tnl_send: number of segment = %d\n", segments->segment_used);


	if (!strcmp(srv6_port->name, "srv6_sys_2154"))
	{  	// encap virtual port
		encap_pure_packet_to_srv6_segments(skb,segments);
	}
	pr_warn("srv6 ovs tnl send call ovs_vport_receive  (vport-gtp.c), skb len = %d\n", skb->len);
	ovs_vport_receive(vport,skb,OVS_CB(skb)->tun_key);
	pr_warn("srv6 ovs tnl send after call ovs_vport_receive  (vport-gtp.c)\n");
	return err;

}
#endif

static void cpy_ipv6(struct in6_addr *in6_dst, struct ipv6_addr *ipv6_src)
{
	in6_dst->in6_u.u6_addr32[0] = ipv6_src->addr[0];
       	in6_dst->in6_u.u6_addr32[1] = ipv6_src->addr[1];
       	in6_dst->in6_u.u6_addr32[2] = ipv6_src->addr[2];
       	in6_dst->in6_u.u6_addr32[3] = ipv6_src->addr[3];
}


static struct sk_buff* encap_pure_packet_to_srv6(struct sk_buff* skb, struct vport *vport)
{
        struct ethhdr* eth_hdr;
        struct ipv6hdr* outer_iph;
	struct ipv6_rt_hdr *srh_ipv6;
        struct ipv6hdr* inner_iph;
        uint8_t sr_header_len = 0;
	struct ipv6_segments *segments = &vport->segments; //BN: READ ONLY?
	int i = 0;
	uint8_t segment_used;
	uint16_t header_size = 0;
	uint16_t full_len = 0;
	unsigned char old_skb_cb[OVS_CB_SIZE];
	unsigned char *data;
	unsigned char *old_skb_data;
	uint16_t old_skb_len;
	uint16_t inner_payload_len = 0;
	struct sk_buff * old_skb;
	struct ipv6_addr *next_segment;
	//struct in6_addr in6_ipv6_addr;

	
	
	if (segments){
		pr_warn("encap_pure_packet_to_srv6: number of segment = %d\n", segments->segment_used);
		for (i = 0; i < segments->segment_used; i++){
			pr_warn("Segment %d: %02x %02x %02x %02x\n", i, segments->ipv6_segments[i].addr[0], segments->ipv6_segments[i].addr[1], segments->ipv6_segments[i].addr[2], segments->ipv6_segments[i].addr[3]);
		}
	}

	old_skb = skb;
	memcpy(&old_skb_cb, skb->cb, OVS_CB_SIZE);
	eth_hdr = (struct ethhdr*)skb->data;
        inner_iph = (struct ipv6hdr*)(eth_hdr+1); //after the ethernet hdr is the inner IP header.
        old_skb_data = (unsigned char*)skb->data;
	old_skb_len = skb->len;

	segment_used = segments->segment_used;
	if (segment_used >= 1)
		sr_header_len = 40 + 8 + 16*segment_used; //Outer IPV6 SR header = outer IPV6 header (40B) + SRH (8B) + 1 IPV6 segment (16B).
	else {
		pr_warn ("No segment was provided. NOT doing encapsulation!\n");
		return skb;
	}

	inner_payload_len = __be16_to_cpu(inner_iph->payload_len);
	full_len = sizeof(*eth_hdr) + sr_header_len +  sizeof(*inner_iph) + inner_payload_len;	//Full_len = ethernet header (14B) + sr_header_len (with segments) + 40B (inner ipv6 header) + inner ipv6 payload len.
	
	skb = alloc_skb(full_len, GFP_ATOMIC);	//Create a new skb, to have enough room for the SR segments. Must use GFP_ATOMIC because this is inside an interrupt.
	skb_reserve(skb, header_size);	//reserve no head room.
	data = skb_put(skb, full_len); 

	//ethernet header
        memcpy(data, old_skb_data, sizeof(*eth_hdr)); //BN: copy the skb's ethernet header over to the new skb_sr.
	old_skb_data += sizeof(*eth_hdr);//Advance the data pointer to not including the ethernet header.
	skb_set_mac_header(skb, 0); //set the MAC address pointer to begining of the extended skb->data.

	//outer ipv6 header with segment routing
        outer_iph = (struct ipv6hdr*) (data+sizeof(*eth_hdr));
        outer_iph->version      = 6;
        memcpy(outer_iph->flow_lbl,inner_iph->flow_lbl,3);
        outer_iph->payload_len  = __cpu_to_be16(sr_header_len + inner_payload_len);  //BN:lenght of this IP packet (including the inner IP packet and inner IPv6 header (40B))
        outer_iph->nexthdr      = 43; //IPV6 routing.
        outer_iph->hop_limit = inner_iph->hop_limit - 1;
	next_segment = &segments->ipv6_segments[0];
	cpy_ipv6(&outer_iph->daddr, next_segment);	//outer ipv6 header's dst is the first segment
        outer_iph->saddr        = tun_src;	//TODO. What to put here?
	//Segment routing with segments
	srh_ipv6 = (struct ipv6_rt_hdr*) (outer_iph+1);
	srh_ipv6->nexthdr = 41; //IPV6
	srh_ipv6->hdrlen = 16*segment_used/8; //size in protocol = 8 + 8*x with x = hdrlen.
	srh_ipv6->type = 4;
	srh_ipv6->segments_left = segment_used-1;
	memset(srh_ipv6+1, 0, sizeof(uint32_t));
	for (i = segment_used-1; i >= 0; i--){
		memcpy(srh_ipv6+2+(segment_used-1-i)*sizeof(struct in6_addr)/4, &segments->ipv6_segments[i], sizeof(struct in6_addr)); //Reversed order
	}

	//original inner ip header
	memcpy(data+sizeof(*eth_hdr)+sr_header_len, old_skb_data, old_skb_len-sizeof(*eth_hdr)); 	//Copy the original skb to the new skb, not copying the ethernet header
        skb_set_network_header(skb,sizeof(*eth_hdr)); //set the IP header pointer, ethernet offset = 14B
	
	//need the old cb
	memcpy(skb->cb, &old_skb_cb, OVS_CB_SIZE);	//Cpy skb->cb over because tunnel key is in there.

	kfree_skb(old_skb);	//Free the old skb
	return skb;
}


/*
static struct sk_buff* encap_pure_packet_to_srv6(struct sk_buff* skb, struct vport *vport)
{
        struct ethhdr* eth_hdr;
        struct ipv6hdr* outer_iph;
        //struct rt2_hdr* srh;
	struct ipv6_rt_hdr *srh_ipv6;
        struct ipv6hdr* inner_iph;
        uint8_t sr_header_len = 0;
	struct ipv6_segments *segments = &vport->segments; //BN: READ ONLY?
	uint8_t i = 0;
	uint8_t segment_used;
	uint8_t offset;
	unsigned char *start_skb;
	//struct sk_buff *skb_sr;
	uint16_t header_size = 0;
	uint16_t full_len = 0;
	unsigned char *data;
	unsigned char *old_skb_data;
	uint16_t inner_payload_len = 0;
	struct sk_buff * old_skb;
	
	//segment_used = segments->segment_used;
	segment_used = 1; //TODO: why would not 3 segments work?
        //BN: TODO: to calculater offset side = outer ipv6 header with SR.
	offset = 40 + 8 + 16*segment_used; //Outer IPV6 SR header = outer IPV6 header (40B) + SRH (8B) + 1 IPV6 segment (16B).
        // get mac layer address -> change MAC ADDRESS AS ENODEB & SGW
        eth_hdr = (struct ethhdr*)skb->data;

	pr_warn("SKB head room = %d\n", skb->data - skb->head);

#ifdef _SR_
	pr_warn("encap_pure_packet_to_srv6: offset = %d,  number of segment = %d\n", offset, vport->segments.segment_used);
#endif
	//pr_warn("skb->cb\n");
	//for (i=0; i < 40; i++){
	//	pr_warn("%02X ", skb->cb[i]);
	//}
        start_skb = (unsigned char*)skb->data;
        memcpy(start_skb-offset, start_skb, sizeof(*eth_hdr)); //BN: copy ethernet header over, and leave space for GTP
        memset(start_skb, 0, sizeof(*eth_hdr)); //BN:clear the copied ethernet header in skb.

        skb_push(skb, offset);  //BN: Add data to the start of the buffer, create room for the IPV6 SRH
	//pr_warn("skb_data = %02x, %02x\n", skb->data, start_skb-offset);
        skb_set_mac_header(skb, 0); //BN: set the MAC address pointer to begining of the extended skb->data.

        inner_iph = (struct ipv6hdr*)(eth_hdr+1); //BN: after the ethernet hdr is the inner IP header.
	//pr_warn("inner start = %02x\n", inner_iph);
        //BN: to create an IPV6 header with SR header
        eth_hdr = (start_skb-offset);   // key point
        outer_iph = (struct ipv6hdr*) (eth_hdr+1);
	//pr_warn("outer_iph start = %02x\n", outer_iph);
        outer_iph->version      = 6;
        memcpy(outer_iph->flow_lbl,inner_iph->flow_lbl,3);
        outer_iph->payload_len  = __cpu_to_be16(offset + __be16_to_cpu(inner_iph->payload_len));  //BN:lenght of this IP packet (including the inner IP packet and inner IPv6 header (40B))
        outer_iph->nexthdr      = 43; //BN: IPV6 routing.
        outer_iph->hop_limit = inner_iph->hop_limit - 1;
        //BN: test only
	//cpy_ipv6(&outer_iph->daddr, &segments->ipv6_segments[0]);
        outer_iph->daddr        = tun_src;
        outer_iph->saddr        = tun_src;
	//BN: SR
	srh_ipv6 = (struct ipv6_rt_hdr*) (outer_iph+1);
	//pr_warn("srh_ipv6 start = %02x\n", srh_ipv6);
	srh_ipv6->nexthdr = 41; //IPV6
	//srh_ipv6->hdrlen = 16*(segment_used-1)/8; //size in protocol = 8 + 8*x with x = hdrlen.
	srh_ipv6->hdrlen = 2; //size in protocol = 8 + 8*x with x = hdrlen.
	srh_ipv6->type = 4;
	//srh_ipv6->segments_left = segment_used-1;
	srh_ipv6->segments_left = 0;

        //srh = (struct rt2_hdr*) (outer_iph+1);
	//srh->rt_hdr.nexthdr = 41; //IPV6
	//srh->rt_hdr.hdrlen = 0x02; //8 + 1 segment (16B) = 24
	//srh->rt_hdr.type = 4;
	//srh->rt_hdr.segments_left = 0;
	//srh->reserved = 0x00000000;	//4B before segment
	//cpy_ipv6(&srh->addr, &segments->ipv6_segments[0]);
        //compute_ip_checksum(outer_iph);       //BN: NO CHECHSUM REQUIRED. TODO, calculate checksum for IPV6 header.
        skb_set_network_header(skb,OFFSET_MAC); //BN:set the IP header pointer, ethernet offset = 14B
	//for (i = 0; i < skb->len; i++){
	//	pr_warn("%02X ",skb->data[i]);
	//}
	//pr_warn("\n");

}
*/

static int ovs_tnl_send(struct vport *vport, struct sk_buff *skb)
{
	int err = 0;
	struct srv6_port *srv6_port = get_srv6_port(vport);
	pr_warn("srv6 ovs tnl send vport name = %s num = %u mac_len = %d, skb len = %d (vport-gtp.c)\n", 
	srv6_port->name, vport->port_no, skb->mac_len, skb->len);

	if (!strcmp(srv6_port->name, "srv6_sys_2154"))
	{  	// encap virtual port
		skb = encap_pure_packet_to_srv6(skb, vport);
		//encap_pure_packet_to_srv6(skb, vport);
	}
	pr_warn("srv6 ovs tnl send call ovs_vport_receive, skb len = %d\n", skb->len);
	ovs_vport_receive(vport,skb,OVS_CB(skb)->tun_key);
	pr_warn("srv6 ovs tnl send after call ovs_vport_receive, skb len = %d\n", skb->len);
	return err;

}


#ifdef _SR_
static int ipv6_segments_send(struct vport *vport, struct sk_buff *skb, struct ipv6_segments *segments)
{
	//int network_offset = skb_network_offset(skb);
	struct ovs_key_ipv4_tunnel tun_key;

		
	if (unlikely(!OVS_CB(skb)->tun_key))
	{
		OVS_CB(skb)->tun_key = &tun_key;
		pr_warn("tunnel key is null (vport_srv6.c)\n");
	}
	else
	{
		pr_warn("tunnel key is not null (vport.c)\n" );
	}

        if (segments)
                pr_warn("ipv6_segments_send: number of segment = %d\n", segments->segment_used);
	/* We only encapsulate IPv4 and IPv6 packets */
	/* ETH_P_IP -> 0X0800
	   ETH_P_IP -> 0X86DD
	   ETH_P_ARP -> 0X0806
	*/
	switch (skb->protocol) {
	case htons(ETH_P_IP):
	case htons(ETH_P_IPV6):
		ovs_tnl_send_segments(vport, skb, segments);
		return 0;
	default:
		pr_warn("srv6 tnl receive unsupported protocol, type = %d \n", skb->protocol);
		kfree_skb(skb);
		return 0;
	}
}
#endif

static int srv6_tnl_send(struct vport *vport, struct sk_buff *skb)
{
	//int network_offset = skb_network_offset(skb);
	struct ovs_key_ipv4_tunnel tun_key;

	if (unlikely(!OVS_CB(skb)->tun_key))
	{
		OVS_CB(skb)->tun_key = &tun_key;
		pr_warn("tunnel key is null\n");
	}
	else
	{
		pr_warn("tunnel key is not null (vport)\n" );
	}

	/* We only encapsulate IPv4 and IPv6 packets */
	/* ETH_P_IP -> 0X0800
	   ETH_P_IP -> 0X86DD
	*/
	switch (skb->protocol) {
	case htons(ETH_P_IP):
	case htons(ETH_P_IPV6):
		ovs_tnl_send(vport, skb);
		return 0;
	default:
		pr_warn("srv6 tnl receive unsupported protocol = %d \n", skb->protocol);
		kfree_skb(skb);
		return 0;
	}
}

static const char *srv6_get_name(const struct vport *vport)
{
	struct srv6_port *srv6_port = get_srv6_port(vport);

	return srv6_port->name;
}

const struct vport_ops ovs_srv6_vport_ops = {
	.type		= OVS_VPORT_TYPE_SRV6,
	.create		= srv6_tnl_create,
	.destroy	= srv6_tnl_destroy,
	.get_name	= srv6_get_name,
	.get_options	= srv6_get_options,
	.send		= srv6_tnl_send,
#ifdef _SR_
	.send_with_segments		= ipv6_segments_send,
#endif
};
