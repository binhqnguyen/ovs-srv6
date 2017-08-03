/*
 * Copyright (c) 2007-2012 Nicira, Inc.
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of version 2 of the GNU General Public
 * License as published by the Free Software Foundation.
 *
 * This program is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
 * General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
 * 02110-1301, USA
 */

#define pr_fmt(fmt) KBUILD_MODNAME ": " fmt

#include <linux/if_arp.h>
#include <linux/if_bridge.h>
#include <linux/if_vlan.h>
#include <linux/kernel.h>
#include <linux/llc.h>
#include <linux/rtnetlink.h>
#include <linux/skbuff.h>
#include <linux/openvswitch.h>

#include <net/llc.h>

#include "datapath.h"
#include "vlan.h"
#include "vport-internal_dev.h"
#include "vport-netdev.h"

#if LINUX_VERSION_CODE < KERNEL_VERSION(2,6,37) && \
	!defined(HAVE_VLAN_BUG_WORKAROUND)
#include <linux/module.h>

static int vlan_tso __read_mostly;
module_param(vlan_tso, int, 0644);
MODULE_PARM_DESC(vlan_tso, "Enable TSO for VLAN packets");
#else
#define vlan_tso true
#endif

static void netdev_port_receive(struct vport *vport, struct sk_buff *skb);

#if LINUX_VERSION_CODE >= KERNEL_VERSION(2,6,39)
/* Called with rcu_read_lock and bottom-halves disabled. */
static rx_handler_result_t netdev_frame_hook(struct sk_buff **pskb)
{
	struct sk_buff *skb = *pskb;
	struct vport *vport;

	if (unlikely(skb->pkt_type == PACKET_LOOPBACK))
		return RX_HANDLER_PASS;

	vport = ovs_netdev_get_vport(skb->dev);

	netdev_port_receive(vport, skb);

	return RX_HANDLER_CONSUMED;
}
#elif LINUX_VERSION_CODE >= KERNEL_VERSION(2,6,36) || \
      defined HAVE_RHEL_OVS_HOOK
/* Called with rcu_read_lock and bottom-halves disabled. */
static struct sk_buff *netdev_frame_hook(struct sk_buff *skb)
{
	struct vport *vport;

	if (unlikely(skb->pkt_type == PACKET_LOOPBACK))
		return skb;

	vport = ovs_netdev_get_vport(skb->dev);

	netdev_port_receive(vport, skb);

	return NULL;
}
#elif LINUX_VERSION_CODE >= KERNEL_VERSION(2,6,32)
/*
 * Used as br_handle_frame_hook.  (Cannot run bridge at the same time, even on
 * different set of devices!)
 */
/* Called with rcu_read_lock and bottom-halves disabled. */
static struct sk_buff *netdev_frame_hook(struct net_bridge_port *p,
					 struct sk_buff *skb)
{
	netdev_port_receive((struct vport *)p, skb);
	return NULL;
}
#else
#error
#endif

#if LINUX_VERSION_CODE >= KERNEL_VERSION(2,6,36) || \
    defined HAVE_RHEL_OVS_HOOK
static int netdev_init(void) { return 0; }
static void netdev_exit(void) { }
#else
static int port_count;

static void netdev_init(void)
{
	port_count++;
	if (port_count > 1)
		return;

	/* Hook into callback used by the bridge to intercept packets.
	 * Parasites we are. */
	br_handle_frame_hook = netdev_frame_hook;

	return;
}

static void netdev_exit(void)
{
	port_count--;
	if (port_count > 0)
		return;

	br_handle_frame_hook = NULL;
}
#endif

static struct net_device *get_dpdev(struct datapath *dp)
{
	struct vport *local;

	local = ovs_vport_ovsl(dp, OVSP_LOCAL);
	BUG_ON(!local);
	return netdev_vport_priv(local)->dev;
}

static struct vport *netdev_create(const struct vport_parms *parms)
{
	struct vport *vport;
	struct netdev_vport *netdev_vport;
	int err;

	vport = ovs_vport_alloc(sizeof(struct netdev_vport),
				&ovs_netdev_vport_ops, parms);
	if (IS_ERR(vport)) {
		err = PTR_ERR(vport);
		goto error;
	}

	netdev_vport = netdev_vport_priv(vport);

	netdev_vport->dev = dev_get_by_name(ovs_dp_get_net(vport->dp), parms->name);
	if (!netdev_vport->dev) {
		err = -ENODEV;
		goto error_free_vport;
	}

	if (netdev_vport->dev->flags & IFF_LOOPBACK ||
	    netdev_vport->dev->type != ARPHRD_ETHER ||
	    ovs_is_internal_dev(netdev_vport->dev)) {
		err = -EINVAL;
		goto error_put;
	}

	rtnl_lock();
	err = netdev_master_upper_dev_link(netdev_vport->dev,
					   get_dpdev(vport->dp));
	if (err)
		goto error_unlock;

	err = netdev_rx_handler_register(netdev_vport->dev, netdev_frame_hook,
					 vport);
	if (err)
		goto error_master_upper_dev_unlink;

	dev_set_promiscuity(netdev_vport->dev, 1);
	netdev_vport->dev->priv_flags |= IFF_OVS_DATAPATH;
	rtnl_unlock();

	netdev_init();
	return vport;

error_master_upper_dev_unlink:
	netdev_upper_dev_unlink(netdev_vport->dev, get_dpdev(vport->dp));
error_unlock:
	rtnl_unlock();
error_put:
	dev_put(netdev_vport->dev);
error_free_vport:
	ovs_vport_free(vport);
error:
	return ERR_PTR(err);
}

static void free_port_rcu(struct rcu_head *rcu)
{
	struct netdev_vport *netdev_vport = container_of(rcu,
					struct netdev_vport, rcu);

	dev_put(netdev_vport->dev);
	ovs_vport_free(vport_from_priv(netdev_vport));
}

static void netdev_destroy(struct vport *vport)
{
	struct netdev_vport *netdev_vport = netdev_vport_priv(vport);

	netdev_exit();
	rtnl_lock();
	netdev_vport->dev->priv_flags &= ~IFF_OVS_DATAPATH;
	netdev_rx_handler_unregister(netdev_vport->dev);
	netdev_upper_dev_unlink(netdev_vport->dev, get_dpdev(vport->dp));
	dev_set_promiscuity(netdev_vport->dev, -1);
	rtnl_unlock();

	call_rcu(&netdev_vport->rcu, free_port_rcu);
}

const char *ovs_netdev_get_name(const struct vport *vport)
{
	const struct netdev_vport *netdev_vport = netdev_vport_priv(vport);
	return netdev_vport->dev->name;
}

/* Must be called with rcu_read_lock. */
static void netdev_port_receive(struct vport *vport, struct sk_buff *skb)
{
	if (unlikely(!vport))
		goto error;

	if (unlikely(skb_warn_if_lro(skb)))
		goto error;

	/* Make our own copy of the packet.  Otherwise we will mangle the
	 * packet for anyone who came before us (e.g. tcpdump via AF_PACKET).
	 * (No one comes after us, since we tell handle_bridge() that we took
	 * the packet.) */
	skb = skb_share_check(skb, GFP_ATOMIC);
	if (unlikely(!skb))
		return;

	skb_push(skb, ETH_HLEN);
	ovs_skb_postpush_rcsum(skb, skb->data, ETH_HLEN);

	ovs_vport_receive(vport, skb, NULL);
	return;

error:
	kfree_skb(skb);
}

static unsigned int packet_length(const struct sk_buff *skb)
{
	unsigned int length = skb->len - ETH_HLEN;

	if (skb->protocol == htons(ETH_P_8021Q))
		length -= VLAN_HLEN;

	return length;
}

static bool dev_supports_vlan_tx(struct net_device *dev)
{
#if LINUX_VERSION_CODE >= KERNEL_VERSION(2,6,37)
	/* Software fallback means every device supports vlan_tci on TX. */
	return true;
#elif defined(HAVE_VLAN_BUG_WORKAROUND)
	return dev->features & NETIF_F_HW_VLAN_TX;
#else
	/* Assume that the driver is buggy. */
	return false;
#endif
}

static int netdev_send(struct vport *vport, struct sk_buff *skb)
{
	struct netdev_vport *netdev_vport = netdev_vport_priv(vport);
	int mtu = netdev_vport->dev->mtu;
	int len;

	pr_warn ("netdev_send: vport = %d\n", vport->port_no);
	if (unlikely(packet_length(skb) > mtu && !skb_is_gso(skb))) {
		net_warn_ratelimited("%s: dropped over-mtu packet: %d > %d\n",
				     netdev_vport->dev->name,
				     packet_length(skb), mtu);
		goto drop;
	}

	skb->dev = netdev_vport->dev;

	if (vlan_tx_tag_present(skb) && !dev_supports_vlan_tx(skb->dev)) {
		int features;

		features = netif_skb_features(skb);

		if (!vlan_tso)
			features &= ~(NETIF_F_TSO | NETIF_F_TSO6 |
				      NETIF_F_UFO | NETIF_F_FSO);

		if (netif_needs_gso(skb, features)) {
			struct sk_buff *nskb;

			nskb = skb_gso_segment(skb, features);
			if (!nskb) {
				if (unlikely(skb_cloned(skb) &&
				    pskb_expand_head(skb, 0, 0, GFP_ATOMIC)))
					goto drop;

				skb_shinfo(skb)->gso_type &= ~SKB_GSO_DODGY;
				goto tag;
			}

			if (IS_ERR(nskb))
				goto drop;
			consume_skb(skb);
			skb = nskb;

			len = 0;
			do {
				nskb = skb->next;
				skb->next = NULL;

				skb = __vlan_put_tag(skb, skb->vlan_proto, vlan_tx_tag_get(skb));
				if (likely(skb)) {
					len += skb->len;
					vlan_set_tci(skb, 0);
					dev_queue_xmit(skb);
				}

				skb = nskb;
			} while (skb);

			return len;
		}

tag:
		skb = __vlan_put_tag(skb, skb->vlan_proto, vlan_tx_tag_get(skb));
		if (unlikely(!skb))
			return 0;
		vlan_set_tci(skb, 0);
	}

	len = skb->len;
	dev_queue_xmit(skb);

	return len;

drop:
	kfree_skb(skb);
	return 0;
}

/* Returns null if this device is not attached to a datapath. */
struct vport *ovs_netdev_get_vport(struct net_device *dev)
{
#if LINUX_VERSION_CODE >= KERNEL_VERSION(2,6,36) || \
    defined HAVE_RHEL_OVS_HOOK
#if IFF_OVS_DATAPATH != 0
	if (likely(dev->priv_flags & IFF_OVS_DATAPATH))
#else
	if (likely(rcu_access_pointer(dev->rx_handler) == netdev_frame_hook))
#endif
#ifdef HAVE_RHEL_OVS_HOOK
		return (struct vport *)rcu_dereference_rtnl(dev->ax25_ptr);
#else
		return (struct vport *)rcu_dereference_rtnl(dev->rx_handler_data);
#endif
	else
		return NULL;
#else
	return (struct vport *)rcu_dereference_rtnl(dev->br_port);
#endif
}

const struct vport_ops ovs_netdev_vport_ops = {
	.type		= OVS_VPORT_TYPE_NETDEV,
	.create		= netdev_create,
	.destroy	= netdev_destroy,
	.get_name	= ovs_netdev_get_name,
	.send		= netdev_send,
};

#if LINUX_VERSION_CODE < KERNEL_VERSION(2,6,36) && \
    !defined HAVE_RHEL_OVS_HOOK
/*
 * Enforces, mutual exclusion with the Linux bridge module, by declaring and
 * exporting br_should_route_hook.  Because the bridge module also exports the
 * same symbol, the module loader will refuse to load both modules at the same
 * time (e.g. "bridge: exports duplicate symbol br_should_route_hook (owned by
 * openvswitch)").
 *
 * Before Linux 2.6.36, Open vSwitch cannot safely coexist with the Linux
 * bridge module, so openvswitch uses this macro in those versions.  In
 * Linux 2.6.36 and later, Open vSwitch can coexist with the bridge module.
 *
 * The use of "typeof" here avoids the need to track changes in the type of
 * br_should_route_hook over various kernel versions.
 */
typeof(br_should_route_hook) br_should_route_hook;
EXPORT_SYMBOL(br_should_route_hook);
#endif
