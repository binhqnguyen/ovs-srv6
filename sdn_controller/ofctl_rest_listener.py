#Copyright Binh Nguyen University of Utah (binh@cs.utah.edu)
#
#Licensed under the Apache License, Version 2.0 (the "License");
#you may not use this file except in compliance with the License.
#You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
#Unless required by applicable law or agreed to in writing, software
#distributed under the License is distributed on an "AS IS" BASIS,
#WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#See the License for the specific language governing permissions and
#limitations under the License.

#!/usr/bin/python
import logging

import json
import ast
import os
from webob import Response

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller import dpset
from ryu.controller.handler import MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_0
from ryu.ofproto import ofproto_v1_2
from ryu.ofproto import ofproto_v1_3
from ryu.lib import ofctl_v1_0
from ryu.lib import ofctl_v1_2
from ryu.lib import ofctl_v1_3
from ryu.app.wsgi import ControllerBase, WSGIApplication
from collections import defaultdict

from northbound_api import North_api
from TE.te_controller import Te_controller

LOG = logging.getLogger('ryu.app.ofctl_rest_listener')
LOG.setLevel(logging.DEBUG)

# supported ofctl versions in this restful app
supported_ofctl = {
    ofproto_v1_0.OFP_VERSION: ofctl_v1_0,
    ofproto_v1_2.OFP_VERSION: ofctl_v1_2,
    ofproto_v1_3.OFP_VERSION: ofctl_v1_3,
}

# REST API LISTENER FOR SR CONTROLLER

class SR_rest_api(app_manager.RyuApp):
    _CONTEXTS = {
        'dpset': dpset.DPSet,
        'wsgi': WSGIApplication
    }
    def __init__(self, *args, **kwargs):
        super(SR_rest_api, self).__init__(*args, **kwargs)
        LOG.debug("Init SR_rest_api")
        self.dpset = kwargs['dpset']
        wsgi = kwargs['wsgi']
        self.waiters = {}
        self.data = {}
        self.data['dpset'] = self.dpset
        self.data['waiters'] = self.waiters
        mapper = wsgi.mapper

        wsgi.registory['North_api'] = self.data
        

        flow_mgmt = "flow_mgmt"
	ospf_monitor = "ospf_monitor"
	ospf_monitor_path = "/%s" % ospf_monitor
        flow_mgmt_path = '/%s' % flow_mgmt
        uri = flow_mgmt_path + '/delete'
        mapper.connect(flow_mgmt, uri,
                       controller=North_api, action='delete_single_flow',
                       conditions=dict(method=['POST']))

        uri = flow_mgmt_path + '/delete_all_flows'
        mapper.connect(flow_mgmt, uri,
                       controller=North_api, action='delete_all_flows',
                       conditions=dict(method=['POST']))


	#Usage: curl --data 'dpid=17779080870&match=ipv6_dst=2001::204:23ff:feb7:1e40,eth_type=0x86DD&actions=ipv6_dst=2001::208:204:23ff:feb7:1e40,ipv6_dst=2001::208:204:23ff:feb7:1e41,ipv6_dst=2001::208:204:23ff:feb7:1e42,output=1' http://0.0.0.0:8080/flow_mgmt/insert
        uri = flow_mgmt_path + '/insert'
        mapper.connect(flow_mgmt, uri,
                       controller=North_api, action='insert_single_flow',
                       conditions=dict(method=['POST']))

        uri = ospf_monitor_path + '/lsa_put'
        mapper.connect(ospf_monitor, uri,
                       controller=Te_controller, action='receive_ospf_lsa',
                       conditions=dict(method=['POST']))

	uri = ospf_monitor_path + '/get_topology'
        mapper.connect(ospf_monitor, uri,
                       controller=Te_controller, action='get_topology',
                       conditions=dict(method=['GET']))




    @set_ev_cls([ofp_event.EventOFPStatsReply,
                 ofp_event.EventOFPDescStatsReply,
                 ofp_event.EventOFPFlowStatsReply,
                 ofp_event.EventOFPAggregateStatsReply,
                 ofp_event.EventOFPTableStatsReply,
                 ofp_event.EventOFPTableFeaturesStatsReply,
                 ofp_event.EventOFPPortStatsReply,
                 ofp_event.EventOFPQueueStatsReply,
                 ofp_event.EventOFPMeterStatsReply,
                 ofp_event.EventOFPMeterFeaturesStatsReply,
                 ofp_event.EventOFPMeterConfigStatsReply,
                 ofp_event.EventOFPGroupStatsReply,
                 ofp_event.EventOFPGroupFeaturesStatsReply,
                 ofp_event.EventOFPGroupDescStatsReply,
                 ofp_event.EventOFPPortDescStatsReply
                 ], MAIN_DISPATCHER)
    def stats_reply_handler(self, ev):
        msg = ev.msg
        dp = msg.datapath

        if dp.id not in self.waiters:
            return
        if msg.xid not in self.waiters[dp.id]:
            return
        lock, msgs = self.waiters[dp.id][msg.xid]
        msgs.append(msg)

        flags = 0
        if dp.ofproto.OFP_VERSION == ofproto_v1_0.OFP_VERSION:
            flags = dp.ofproto.OFPSF_REPLY_MORE
        elif dp.ofproto.OFP_VERSION == ofproto_v1_2.OFP_VERSION:
            flags = dp.ofproto.OFPSF_REPLY_MORE
        elif dp.ofproto.OFP_VERSION == ofproto_v1_3.OFP_VERSION:
            flags = dp.ofproto.OFPMPF_REPLY_MORE

        if msg.flags & flags:
            return
        del self.waiters[dp.id][msg.xid]
        lock.set()

    @set_ev_cls([ofp_event.EventOFPSwitchFeatures,
                 ofp_event.EventOFPQueueGetConfigReply], MAIN_DISPATCHER)
    def features_reply_handler(self, ev):
        msg = ev.msg
        dp = msg.datapath

        if dp.id not in self.waiters:
            return
        if msg.xid not in self.waiters[dp.id]:
            return
        lock, msgs = self.waiters[dp.id][msg.xid]
        msgs.append(msg)

        del self.waiters[dp.id][msg.xid]
        lock.set()




