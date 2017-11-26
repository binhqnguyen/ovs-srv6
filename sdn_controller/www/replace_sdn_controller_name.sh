#!/bin/bash

if [ $# -ne 1 ]; then
	echo "Usage: <SDN controller, eg, node1.srv6-test1.phantomnet.emulab.net>"
	exit 1
fi
sudo cp web-portal/te_app.template.js web-portal/te_app.js
sudo cp web-portal/index.template.html web-portal/index.html
sudo sed -i s/SDN_CONTROLLER/$1/ web-portal/te_app.js
sudo sed -i s/SDN_CONTROLLER/$1/ web-portal/index.html
