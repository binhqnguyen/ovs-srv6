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


LOG = logging.getLogger('ryu.app.North_api')
LOG.setLevel(logging.INFO)

class North_api(ControllerBase):
	def __init__(self, req, link, data, **config):
		super(North_api, self).__init__(req, link, data, **config)

	#NORTH BOUND API - REST
	def delete_single_flow(self, req, **_kwargs):
		post = req.POST
		M = Match()
    		if len(post) < 2 or "dpid" not in post:
        		LOG.info("INVALID POST values: %s" % post)
        		return Response(status=404)

		match = M.parse_match_fields(post['match'])
        	dpid = post['dpid']
        
		LOG.debug("RECEIVED NB API: delete_single_flow: (dpid, match) = (%s, %s)" % (dpid, match) )
        	if SR_flows_mgmt.delete_single_flow(dpid, match):
			return Response(status=200)
        	return Response(status=500)

	#Usage: curl --data "dpid=12345&match=123,456&actions=src_ip=1,dst_ip=2" http://0.0.0.0:8080/flow_mgmt/insert
	def insert_single_flow(self, req, **_kwargs):
        	post = req.POST
		A = Actions()
		M = Match()
		SR = SR_flows_mgmt()

            	if len(post) < 3 or "actions" not in post or "dpid" not in post:
                	LOG.info("INVALID POST values: %s" % post)
               		return Response(status=404)
        	actions = A.parse_actions_fields(post['actions'])
        	match = M.parse_match_fields(post['match'])
        	dpid = post['dpid']
        	priority = 0
        	if 'priority' in post:
            		priority = int(post['priority'])

            	LOG.debug("RECEIVED NB_API: insert_single_flow: (dpid, match, actions) = (%s,%s,%s)" % (dpid, match, actions)) 
		if not actions or not match:
			LOG.error("Actions or match fields are empty: actions = %s, match = %s" % (actions, match))
			return Response(status = 500)
        	if not SR.insert_single_flow(dpid, priority, match, actions):
			LOG.info("Inserted flow.")
          		return Response(status=200)
		else:
			LOG.error("Can't insert single flow!")
        		return Response(status=500)

    #NORTH BOUND API - REST
    	def delete_all_flows(self, req, **_kwargs):
        	post = req.POST
            	if len(post) < 1 or "dpid" not in post:
                	LOG.info("INVALID POST values: %s" % post)
                	return Response(status=404)

        	dpid = post['dpid']
        
        	if DEBUG:
            		LOG.debug("RECEIVED NB API: delete_all_flows: (dpid) = (%s)" % (dpid) )
        	if SR_flows_mgmt.delete_all_flows(dpid):
          		return Response(status=200)
        	return Response(status=500)



