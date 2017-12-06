
###A. Overview:
This tutorial walks you through steps to set up and use a traffic engineer platform enabled by [Segment Routing](http://www.segment-routing.net/) and Software Defined Networking.
 
At the end of the tutorial, you'll have a sense of how Segment Routing works with SDN and a conventional distributed routing protocol (i.e., OSPF) to realize path implementation in an OSPF network.

This tutorial is developed by Binh Nguyen (binh@cs.utah.edu) when he is with the University of Utah.

#####Software:
The software developed for this tutorial consists of:

* **[An extended Open vSwitch](https://gitlab.flux.utah.edu/safeedge/ovs-srv6)**: extended data plane and an extended OpenFlow protocol to enable Segment Routing encapsulation.
* **[OSPF monitor daemon](https://gitlab.flux.utah.edu/safeedge/sripv6-linux/tree/master/ospf_monitor)**: runs on each OSPF router (i.e., routers 2,3,4,7) and listens to OSPF Link State Advertisements (LSA) to extract real-time topology of the OSPF network.
* **[An SDN controller](https://gitlab.flux.utah.edu/safeedge/ovs-srv6/tree/master/sdn_controller)**: the controller is responsible for (1) generating network topology using the OSPF LSAs, (2) exposing a north bound API for applications to implement traffic engineer paths on the software defined infrastructure. 

	![image](http://www.cs.utah.edu/~binh/archive/segment_routing/img/tutorial_software.png =600x)

	Fig. Segment Routing Framework software.

#####Demo scenarios:

* **Scenario #1:** Connectivity using **Vanilla OSPF shortest path**. Traffic going from `host1` to `host2` via the shortest path.

	![image](http://www.cs.utah.edu/~binh/archive/segment_routing/img/tutorial_scenario_1.png =400x)

	Fig. Demo scenario 1.

* **Scenario #2:** Connectivity using **Segmented routing**. Instead of using the shortest path, traffic going from `host1` to `host2` goes via routers `2->4->3` (using *node segments*) and the reversed path uses `3->2` (using *adjacent segments*).

	![image](http://www.cs.utah.edu/~binh/archive/segment_routing/img/tutorial_scenario_2.png =400x)

	Fig. Demo scenario 2.

###B. Before you continue:

**1. This tutorial is developed using the [Emulab testbed](https://www.emulab.net/portal/) which provides the topology and the repeatable environment for the scripts described in this tutorial.**

**2. To use the testbed, please refer to [this](http://emulab.net/wikidocs/wiki/AdminPolicies).**

###C. Network topology and experiment profile:
**1. Network topology:**

 ![image](http://www.cs.utah.edu/~binh/archive/segment_routing/img/tutorial_topology.png =500x)
 
 Fig. Network topology.
 
 The network topology consists of:
 
 * Two end-hosts (i.e., host1 and host2).
 * Four core routers running OSPF [Free Range Routing](https://frrouting.org/): routers `2, 3, 4, 7` in the Figure.
 * Two Open vSwitches (OVS) attached to two of the core routers. The OVSes runs as L2-bridges by default (i.e., without more specific OF rules).
 * An SDN controller. 
 	

**2. Experiment profile:** 
There is an [Emulab profile](https://www.emulab.net/portal/instantiate.php?profile=srv6-ovs&project=SafeEdge) that describes the above topology and it is packed with the environment to conduct this tutorial. It is highly recommended to use the profile for this tutorial. Otherwise, you'll need to set up the topology yourself and ensure that OSPF and Segment Routing are enabled on the OSPF routers.

**3. Instantiate an experiment using the profile:** login to the [Emulab web portal](http://emulab.net/portal/) and instantiate an experiment using the profile link above. This is the web portal showing the experiment after instantiation:
 ![image](http://www.cs.utah.edu/~binh/archive/segment_routing/img/tutorial_profile.png =600x)

 Fig. Experiment portal in Emulab.

####**Note: All of the scripts in this tutorial run on `node 1` of your experiment.**
###D. Fetching the scripts to run the demo:
    cd ~; git clone git@gitlab.flux.utah.edu:safeedge/sripv6-linux.git
###E. Configure OSPF routers and assign IPv6 addresses:
1. Change to the scripts director:
        cd ~/sripv6-linux/frr-ovs-new
2. Obtain interfaces information of all nodes in the experiment:
        cd ~/sripv6-linux/frr-ovs-new; ./get_all_info.sh
  See `net_info.sh` for the results. Also copy the `net_info.sh` file to `/opt/` folder.
        sudo cp net_info.sh /opt/
3. Add global IPv6 addresses to interfaces on nodes:
        cd ~/sripv6-linux/frr-ovs-new; ./add_global_ipv6.sh
4. Create and install configuration files for Free Range Routing (FRR) OSPF and Zebra deamons:
        cd ~/sripv6-linux/frr-ovs-new; ./create_all_zebra_conf.sh
        cd ~/sripv6-linux/frr-ovs-new; ./create_all_ospf_conf.sh
5. Making the OSPF routers the default gateways for the two end-hosts:
        ./install_default_route_on_hosts.sh
6. Enable Segment Routing (SR) on core routers' interfaces:
        ./enable_sr_flags.sh
        
###F. Run Open vSwitches:
        ./start_all_ovs.sh
###G. Start OSPF monitors:
        cd ~/sripv6-linux/ospf_monitor; ./start_all_ospf_monitor.sh
###H. Start SDN controller and OSPF routers:
***Note: The SDN controller must runs *after* the OSPF deamons***

1. Start SDN controller:
        cd /opt/openvswitch/sdn_controller/; ryu-manager sr_controller_test.py
    You should see the SDN controller prints this *before* moving on:
    
        New OVS connected: 3, still waiting for 0 OVS to join ...
        Init SR_rest_api
        Datapath objects:
        {2: <ryu.controller.controller.Datapath object at 0x2cf4a50>, 3: <ryu.contro.controller.Datapath object at 0x2cfd550>}
        Northbound REST started!
2. Open another terminal on `node 1` and start OSPF deamons on OSPF routers:

        cd ~/sripv6-linux/frr-ovs-new; ./start_all_frr.sh
    After about 30 seconds, the routes are computed on each OSPF router. You could see the routes on node 2,3,4 by logging in a node (e.g., `node 2`) and type `ip -6 route`.

###I. Demo #1 - connectivity with vanilla OSPF :
After the routes are computed by the OSPF routers, *node 0 (i.e., host1) can ping *node 6* (i.e., host2). Get *node 6*'s IPv6 address in the `/opt/net_info.sh` file (look for `n6_2` in the `net_info.sh` file on *node 1*). Then login to *node 0* and ping *node 6*:

        ping6 <node6's IPv6 address>

Note that the connectivity is now provided by the **vanilla OSPF** (i.e., shortest path routing). You should see around *10ms RTT* for the PING traffic.

###J. Demo #2 - Path implementation with the Segment Routing web portal:
1. Prepare the web portal code on *node 1*:
        cd /opt/openvswitch/sdn_controller/www; hostname | xargs ./replace_sdn_controller_name.sh
2. Install the web portal on *node 1*:
        sudo cp -r /opt/openvswitch/sdn_controller/www /var/
3. Access the web portal: open a web browser, enter the ulr: `http://<node1 name>/web-portal/`. The web portal should look like this:
![image](http://www.cs.utah.edu/~binh/archive/segment_routing/img/tutorial_webportal.png =600x)

4. The web portal shows the topology of your OSPF routers. You can also implement a path using the portal.
    For example, to implement a path from *router 2* to *router 3* using node segments `2->4->3` for the `2->3` path and adjacent segments `3->2` for the reversed path:
    * Step 1: enter `2` in the `From` field. Enter `3` in the `To` field.
    * Step 2: Implement source-to-destination (ie, 2->3) path: add 3 *node segments* `2,3,4`, each in a box, under the `Src-Dst Segments`.
    * Step 3: Implement destination-to-source (ie, 3->2) path: add 2 *adjacent segments* `3,2`, each in a box, under the `Dst-Src Segments`.
    * Step 4: enter the SDN controller address in the `SDN controller` field. In this case, the SDN controller is `node 1`'s hostname.
    * Step 5: click `Submit`.
    
After clicking `Submit`, the web-portal will interact with the SDN controller to implement the specified path. The SDN controller should show that it installed an OpenFlow rule on  the switches, ie, you should see something like this:

        155.97.234.128 - - [25/Nov/2017 12:38:08] "POST /flow_mgmt/insert HTTP/1.1" 200 256 0.003696
    
To test the connectivity, login to *node 0* and PING *node 6* as in step *F*, you should see *15ms* RTT in this case (10ms for 2->3 path and 5ms 3->2 path).
    You can also implement other paths by following the above steps.
###K. Demo #3 (optional) - Network topology update when a link fails:
When an interface or a link in the OSPF network fails, the SDN controller will be notified and it will update the topology accordingly.

To turn down a link, login to router 2 (`node 2`) and turn down an interface, e.g.:

		sudo ifconfig eth2 down
		
After around 10s, refresh the web-portal. You'll see that the network topology is now changed:
	![image](http://www.cs.utah.edu/~binh/archive/segment_routing/img/tutorial_linkdown.png =600x)

###L. Contact:
If you have questions, contact Binh Nguyen (luminbinh@gmail.com or binh@cs.utah.edu). Upstream merges are welcome! 