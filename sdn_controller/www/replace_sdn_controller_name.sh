#!/bin/bash

if [ $# -ne 1 ]; then
	echo "Usage: <SDN controller, eg, node1.srv6-test1.phantomnet.emulab.net>"
	exit 1
fi
sudo sed -i s/SDN_CONTROLLER/$1/ web-portal/te_app.js
sudo sed -i s/SDN_CONTROLLER/$1/ web-portal/index.html
