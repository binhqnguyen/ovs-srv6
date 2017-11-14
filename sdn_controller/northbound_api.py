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
from ospf_monitor import *
import json


LOG = logging.getLogger('ryu.app.North_api')
LOG.setLevel(logging.INFO)
HEADERS = {
                        'Access-Control-Allow-Origin': '*',
                        'Access-Control-Allow-Methods': 'GET, POST',
                        'Access-Control-Allow-Headers': 'Origin, Content-Type',
                        'Content-Type':'application/json'}

class North_api(ControllerBase):
	def __init__(self, req, link, data, **config):
		super(North_api, self).__init__(req, link, data, **config)

	#NORTH BOUND API - REST
	def delete_single_flow(self, req, **_kwargs):
		post = req.POST
		M = Match()
                SR = SR_flows_mgmt()
    		if len(post) < 2 or "dpid" not in post:
        		LOG.info("INVALID POST values: %s" % post)
        		return Response(status=404, headers=HEADERS)

		match = M.parse_match_fields(post['match'])
        	dpid = post['dpid']
        	priority = 0
        	if 'priority' in post:
            		priority = int(post['priority'])


		LOG.debug("RECEIVED NB API: delete_single_flow: (dpid, match) = (%s, %s)" % (dpid, match) )
        	if SR.delete_single_flow(dpid, priority, match):
			LOG.info("Deleted a flow.")
			return Response(status=200, headers=HEADERS)
        	return Response(status=500, headers=HEADERS)

	def handle_http_options(self, req, **_kwargs):
                return Response(content_type='application/json', headers=HEADERS)

	#Usage: curl --data "dpid=12345&match=123,456&actions=src_ip=1,dst_ip=2" http://0.0.0.0:8080/flow_mgmt/insert
	def insert_single_flow(self, req, **_kwargs):
        	post = req.POST
		A = Actions()
		M = Match()
		SR = SR_flows_mgmt()
            	if len(post) < 3 or "actions" not in post or "dpid" not in post:
                	LOG.info("INVALID POST values: %s" % post)
               		return Response(status=404, headers=HEADERS)
        	actions = A.parse_actions_fields(post['actions'])
        	match = M.parse_match_fields(post['match'])
        	dpid = post['dpid']
        	priority = 0
        	if 'priority' in post:
            		priority = int(post['priority'])

            	LOG.debug("RECEIVED NB_API: insert_single_flow: (dpid, match, actions) = (%s,%s,%s)" % (dpid, match, actions)) 
		if not actions or not match:
			LOG.error("Actions or match fields are empty: actions = %s, match = %s" % (actions, match))
			return Response(status = 500, headers=HEADERS)
        	if not SR.insert_single_flow(dpid, priority, match, actions):
			LOG.info("Inserted a flow.")
          		return Response(status=200, headers=HEADERS)
		else:
			LOG.error("Can't insert a flow!")
        		return Response(status=500, headers=HEADERS)

        #NORTH BOUND API - REST
    	def delete_all_flows(self, req, **_kwargs):
        	post = req.POST
		SR = SR_flows_mgmt()
            	if len(post) != 1 or "dpid" not in post:
                	LOG.info("INVALID POST values: %s" % post)
                	return Response(status=404, headers=HEADERS)

        	dpid = post['dpid']
        
            	LOG.debug("RECEIVED NB API: delete_all_flows: (dpid) = (%s)" % (dpid) )
        	if SR.delete_all_flows(dpid):
			LOG.info("Deleted all flows in switch %s." % dpid)
          		return Response(status=200, headers=HEADERS)
        	return Response(status=500, headers=HEADERS)

	#NORTH BOUND API - OSPF MONITOR
	def receive_ospf_lsa(self, req, **_kwargs):
		post = req.POST
		#ospf_monitor = OSPF_monitor()
		#LOG.info("post len = %s" % len(post))
		for k in post:
			LOG.info("post[%s]=%s" % (k, post[k]));
		LOG.info("RECEIVED NB API: receive_ospf_lsa: %s" % post)
		#LOG.info("RECEIVED NB API: receive_ospf_lsa")
		return Response(status=500)


