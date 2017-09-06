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

LOG = logging.getLogger('ryu.app.ofctl_rest_listener')
LOG.setLevel(logging.INFO)
DEBUG = 1

class North_api(ControllerBase):
	def __init__(self, req, link, data, **config):
		super(North_api, self).__init__(req, link, data, **config)
		#super(North_api, self).__init__(args, kwargs)

	#NORTH BOUND API - REST
	def delete_single_flow(self, req, **_kwargs):
		post = req.POST
    		if len(post) != 2 or "src_ip" not in post or "dst_ip" not in post:
        		LOG.info("INVALID POST values: %s" % post)
        		return Response(status=404)

    		src_ip = post['src_ip']
		dst_ip = post['dst_ip']
		if DEBUG:
			LOG.debug("RECEIVED NB API: delete_single_flow")
		return Response(status=200)

	#Usage: curl --data "src_ip=1&dst_ip=2" http://0.0.0.0:8080/sr/insert
	def insert_single_flow(self, req, **_kwargs):
		post = req.POST
    		if len(post) != 2 or "src_ip" not in post or "dst_ip" not in post:
        		LOG.info("INVALID POST values: %s" % post)
        		return Response(status=404)

    		src_ip = post['src_ip']
		dst_ip = post['dst_ip']
		if DEBUG:
			LOG.debug("RECEIVED NB API: insert_single_flow")




